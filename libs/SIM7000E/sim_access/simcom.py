#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# simcom.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 10:05:20 AM

import re
import time
import logging

from libs.SIM7000E.sim_access.ATCommands import ATCommands
from libs.SIM7000E.sim_access.adapter import AdapterBase, SerialAdapter, MAPS6Adapter


logger = logging.getLogger('maps6')


class SIMModuleBase(object):

    def __init__(self, adapter):
        assert isinstance(adapter, AdapterBase)
        self.adapter = adapter
        self.check_module_exist()
        self.__initialize()
        self.data_available_flag = False

    def check_module_exist(self):
        if(self.test_module()):
            return True

    def __initialize(self):
        try:
            count = 0
            while count < 10 and not self.module_checkready():
                logger.debug('waiting SIM module to be ready...')
                count += 1
                time.sleep(1)
            logger.info('SIM module is ready.')
            if count >= 10:
                raise Exception('module not ready')
        except Exception as e:
            error = str(e)
            if(error == 'Failed'):
                raise Exception('module not ready')
        tmp = ATCommands.module_setecho(False)
        self.adapter.write(tmp.encode())
        self.wait_ok()

    def wait_ok(self):
        return self.wait_key('OK\r\n')

    def wait_key(self, key, timeout=2000):
        done = False
        msgs = []
        timeout = time.time() + (timeout / 1000)
        while done == False and time.time() < timeout:
            line = self.adapter.readline()
            line = line.decode()
            logger.debug(line)
            msgs.append(line)
            if line == str(key):
                done = True
            elif line == 'ERROR\r\n':
                done = False
                raise Exception('Failed')
            elif line == '+CIPRXGET: 1\r\n':
                self.data_available_flag = True
            elif line == '':
                time.sleep(0.2)
        if not done:
            raise Exception('No reply')
        return msgs

    def test_module(self):
        ''' test module
        '''
        tmp = ATCommands.test()
        self.adapter.write(tmp.encode())
        self.wait_ok()
        return True

    def module_checkready(self):
        ''' check if module is ready
        '''
        tmp = ATCommands.module_checkready()
        self.adapter.write(tmp.encode())
        tmp = self.wait_ok()
        for i in tmp:
            if i.find('+CPIN: READY') == 0:
                return True
        return False

    def network_Deact_PDP(self):
        ''' Deactivate GPRS PDP Context
        '''
        tmp = ATCommands.shut_PDP()
        self.adapter.write(tmp.encode())
        self.wait_key('SHUT OK\r\n', 15000)

    def network_getapn(self):
        ''' get apn
        '''
        tmp = ATCommands.get_apn()
        self.adapter.write(tmp.encode())
        msgs = self.wait_ok()
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
        self.adapter.write(tmp.encode())
        self.wait_ok()

    def network_attach(self):
        ''' attach up network
        '''
        tmp = ATCommands.network_attach()
        self.adapter.write(tmp.encode())
        self.wait_ok()

    def network_bringup(self):
        ''' bring up network
        '''
        tmp = ATCommands.network_bringup()
        self.adapter.write(tmp.encode())
        self.wait_ok()

    def network_ipaddr(self):
        ''' get local ip address
        '''
        tmp = ATCommands.network_ipaddr()
        self.adapter.write(tmp.encode())
        tmp = '\r\n'
        while tmp == '\r\n':
            tmp = self.adapter.readline(timeout=500)
            tmp = tmp.decode()
        re_result = re.search('\d+.\d+.\d+.\d+', tmp)
        if(re_result):
            return re_result.group()
        return ''

    def network_chkAttach(self):
        ''' check attach status
        '''
        tmp = ATCommands.read_network_attach()
        self.adapter.write(tmp.encode())
        msgs = self.wait_ok()
        for msg in msgs:
            re_result = re.search('\+CGATT: ([0-1])', msg)
            if(re_result):
                assert len(re_result.groups()) == 1
                state = re_result.group(1)
                return (state == '1')
        return ""

    def network_getCsq(self):
        ''' check CSQ
        '''
        tmp = ATCommands.csq()
        self.adapter.write(tmp.encode())
        msgs = self.wait_ok()
        for msg in msgs:
            re_result = re.search('\+CSQ: ([\d]+),([\d]+)', msg)
            if(re_result):
                assert len(re_result.groups()) == 2
                rssi = re_result.group(1)
                # ber = re_result.group(2)
                return rssi
        return ""

    def get_gps_info(self):
        ''' get GPS info
        '''
        tmp = ATCommands.Gnss_Pwr_on()
        self.adapter.write(tmp.encode())
        self.wait_ok()

        tmp = ATCommands.Gnss_Navigation_info()
        self.adapter.write(tmp.encode())
        msgs = self.wait_ok()

        for msg in msgs:
            re_result = re.search('\+CGNSINF: ([\S]+)', msg)
            if(re_result):
                assert len(re_result.groups()) == 1
                info = re_result.group(1)
                return info
        return ""
        


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    adapter = MAPS6Adapter('COM8')

    try:
        sim = SIMModuleBase(adapter)
        sim.module_checkready()
        while(not sim.network_chkAttach()):
            print('wait connect bs...')
        rssi = sim.network_getCsq()
        print('CSQ: {}'.format(rssi))
        sim.network_Deact_PDP()
        apn = sim.network_getapn()
        sim.network_setapn(apn)
        sim.network_bringup()
        addr = sim.network_ipaddr()
        print('My IP: {0}'.format(addr))
        sim.network_Deact_PDP()
    except Exception as e:
        error = str(e)
        print(error)
