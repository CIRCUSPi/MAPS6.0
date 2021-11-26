#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# simcom.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 10:05:20 AM

import binascii
import logging
import os
import sys
import threading
import time
import re
from abc import ABCMeta, abstractmethod

import six

from sim_access.adapter import AdapterBase, SerialAdapter
from sim_access.ATCommands import ATCommands

logger = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class SIMModuleBase(object):

    def __init__(self, adapter):
        assert isinstance(adapter, AdapterBase)
        self.__adapter = adapter
        self.__initialize()
        self.__parse_table = {
        }

    def __initialize(self):
        cmds = [
            'AT',  # test if basic function is working
            'ATE0',  # no echo is needed
            # 'AT+CMGF=1',  # we want to run in text mode
        ]
        count = 0
        while count < 10 and not self.module_checkready():
            logger.debug('waiting SIM module to be ready...')
            count += 1
            time.sleep(1)
        logger.info('SIM module is ready.')
        if count >= 10:
            raise Exception('module not ready')
        for i in cmds:
            self.__adapter.write('{0}\r\n'.format(i).encode())
            self.__wait_ok()
        self.__network_up = False

    def __wait_ok(self):
        done = False
        counter = 0
        msgs = []
        while done == False and counter < 3:
            line = self.__adapter.readline()
            line = line.decode()
            logger.debug(line)
            msgs.append(line)
            if line == 'OK\r\n':
                done = True
            elif line == 'ERROR\r\n':
                done = False
                raise Exception('Failed')
            if line is None or line == '':
                counter += 1
        if not done:
            raise Exception('No OK reply')
        return msgs

    def module_checkready(self):
        ''' check if module is ready
        '''
        tmp = ATCommands.module_checkready()
        self.__adapter.write(tmp.encode())
        tmp = self.__wait_ok()
        for i in tmp:
            if i.find('+CPIN: READY') == 0:
                return True
        return False

    def network_getapn(self):
        ''' get apn
        '''
        tmp = ATCommands.get_apn()
        self.__adapter.write(tmp.encode())
        msgs = self.__wait_ok()
        for msg in msgs:
            re_result = re.search('\+CGNAPN: ([0-1]),"([\w.]+)"', msg)
            if(re_result):
                assert len(re_result.groups()) == 2
                valid = re_result.group(1)
                apn = re_result.group(2)
                return apn
        return ""

    def network_setapn(self, apn):
        ''' set up APN for network access
        '''
        tmp = ATCommands.network_setapn(apn)
        self.__adapter.write(tmp.encode())
        self.__wait_ok()

    def network_attach(self):
        ''' attach up network
        '''
        tmp = ATCommands.network_attach()
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        time.sleep(2)

    def network_bringup(self):
        ''' bring up network
        '''
        tmp = ATCommands.network_bringup()
        self.__adapter.write(tmp.encode())
        self.__wait_ok()
        self.__network_up = True

    def network_ipaddr(self):
        ''' get local ip address
        '''
        tmp = ATCommands.network_ipaddr()
        self.__adapter.write(tmp.encode())
        tmp = '\r\n'
        while tmp == '\r\n':
            tmp = self.__adapter.readline()
            tmp = tmp.decode()
        return re.search('\d+.\d+.\d+.\d+', tmp).group()

    def mainloop(self, detached=False):
        ''' Currently we are doing nothing here except
            joining the thread
        '''
        self.__monitorthread = threading.Thread(target=self.__monitor_loop)
        self.__monitorthread.start()
        if not detached:
            try:
                self.__monitorthread.join()
            except KeyboardInterrupt:
                logger.info('Exiting...')
                os._exit(0)

    def loop_once(self):
        ''' This is doing the same as mainloop, but just once
        '''
        self.__loop_task()

    def __process_data(self, line):
        for k, v in six.iteritems(self.__parse_table):
            if line.find(k) == 0:
                try:
                    v(line)
                except Exception as e:
                    logger.error(str(e))
                break

    def __loop_task(self):
        try:
            line = self.__adapter.readline()
            line = line.decode()
            self.__process_data(line)
        except Exception as e:
            logger.error(str(e))
            sys.exit(0)

    def __monitor_loop(self):
        while True:
            self.__loop_task()
