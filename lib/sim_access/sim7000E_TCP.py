#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# sim7000E_TCP.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 4:03:34 PM

import sys
sys.path.append('lib\\sim_access')

import re
from ATCommands import ATCommands
from adapter import AdapterBase, SerialAdapter
from simcom import SIMModuleBase
import logging


logger = logging.getLogger(__name__)


class SIM7000E_TPC(SIMModuleBase):
    def __init__(self, adapter):
        assert isinstance(adapter, AdapterBase)
        while(True):
            try:
                super().__init__(adapter)
                break
            except Exception as e:
                error = str(e)
                if(error == 'No reply'):
                    logger.info('module No reply, reset module ...')
                    raise Exception('reset module')
                elif(error == 'module not ready'):
                    logger.info('module not ready, please wait ...')
                else:
                    logger.error('Unknown exception: {}'.format(error))
                    raise Exception('Unknown exception: {}'.format(error))

    def connect(self, ip, port):
        ''' Connect TCP socket
        '''
        assert isinstance(ip, str)
        assert isinstance(port, int)
        while(True):
            try:
                self.network_Deact_PDP()
                tmp = ATCommands.tcp_setRxGet_Manual()
                self.adapter.write(tmp.encode())
                self.wait_ok()
                tmp = ATCommands.tcp_setTxHex()
                self.adapter.write(tmp.encode())
                self.wait_ok()
                apn = self.network_getapn()
                logger.debug('APN: {}'.format(apn))
                self.network_setapn(apn)
                self.network_bringup()
                local_ip = self.network_ipaddr()
                logger.debug('local ip: '.format(local_ip))
                tmp = ATCommands.tcp_connect(ip, port)
                self.adapter.write(tmp.encode())
                self.wait_key('CONNECT OK\r\n', timeout=800000)
                break
            except Exception as e:
                error = str(e)
                if(error == 'No reply'):
                    logger.warning('reset module ...')
                    raise Exception('reset module')
                elif(error == 'Failed'):
                    logger.warning('module response error, try again ...')
                else:
                    logger.error('Unknown exception: {}'.format(error))
                    raise Exception('Unknown exception')
        logger.info('TCP is Connected.')

    def disconnect(self):
        ''' Disconnect TCP socket
        '''
        while(True):
            try:
                self.network_Deact_PDP()
                break
            except Exception as e:
                error = str(e)
                if(error == 'No reply'):
                    logger.warning('reset module ...')
                    raise Exception('reset module')
                elif(error == 'Failed'):
                    logger.warning('module response error, try again ...')
                else:
                    logger.error('Unknown exception: {}'.format(error))
                    raise Exception('Unknown exception')
        logger.info('TCP is Disconnected.')

    def sendData(self, data):
        ''' Send packets via TCP Socket
        '''
        assert isinstance(data, str)
        while(True):
            try:
                tmp = ATCommands.tcp_send(int(len(data) / 2))
                self.adapter.write(tmp.encode())
                self.wait_key('> ')
                self.adapter.write(data.encode())
                self.wait_key('SEND OK\r\n', 10000)
                break
            except Exception as e:
                error = str(e)
                if(error == 'No reply'):
                    logger.warning('reset module ...')
                    raise Exception('reset module')
                elif(error == 'Failed'):
                    logger.warning('module response error, try again ...')
                else:
                    logger.error('Unknown exception: {}'.format(error))
                    raise Exception('Unknown exception')
        logger.info('TCP send success.')

    def available(self):
        ''' Return the length of the TCP Socket receiving buffer
        '''
        while(True):
            try:
                tmp = ATCommands.tcp_chkData()
                self.adapter.write(tmp.encode())
                msgs = self.wait_ok()
                for msg in msgs:
                    re_result = re.search('\+CIPRXGET: 4,([\d]+)', msg)
                    if(re_result):
                        assert len(re_result.groups()) == 1
                        data_len = re_result.group(1)
                        logger.debug('data available {} byte'.format(data_len))
                        return int(data_len)
                assert Exception('The response exceeded expectations')
            except Exception as e:
                error = str(e)
                if(error == 'No reply'):
                    logger.warning('reset module ...')
                    raise Exception('reset module')
                elif(error == 'Failed'):
                    logger.warning('module response error, try again ...')
                else:
                    logger.error('Unknown exception: {}'.format(error))
                    raise Exception('Unknown exception')

    def readData(self, data_len):
        ''' Read packets from TCP Socket
            Return HEX Packets
        '''
        assert isinstance(data_len, int)
        while(True):
            try:
                tmp = ATCommands.tcp_readHEXData(data_len)
                self.adapter.write(tmp.encode())
                msgs = self.wait_ok()
                for idx, msg in enumerate(msgs):
                    re_result = re.search(
                        '\+CIPRXGET: 3,{},([\d]+)'.format(data_len), msg)
                    if(re_result):
                        assert len(re_result.groups()) == 1
                        cnf_len = re_result.group(1)
                        logger.debug('read {} byte'.format(data_len))
                        logger.debug('cnflength {} byte'.format(cnf_len))
                        data = msgs[idx + 1]
                        re_result = re.search('\w+', data)
                        if(re_result):
                            return re_result.group()
                        return ''
                assert Exception('The response exceeded expectations')
            except Exception as e:
                error = str(e)
                if(error == 'No reply'):
                    logger.warning('reset module ...')
                    raise Exception('reset module')
                elif(error == 'Failed'):
                    logger.warning('module response error, try again ...')
                else:
                    logger.error('Unknown exception: {}'.format(error))
                    raise Exception('Unknown exception')

    def connected(self):
        ''' Check TCP is connected
        '''
        while(True):
            try:
                tmp = ATCommands.tcp_status()
                self.adapter.write(tmp.encode())
                msgs = self.wait_key('STATE: ')
                for msg in msgs:
                    re_result = re.search('STATE: ([A-Z]+)', msg)
                    if(re_result):
                        assert len(re_result.groups()) == 1
                        status = re_result.group(1)
                        logger.debug('tcp status: {}'.format(status))
                        logger.info('TCP Status: {}'.format(status))
                        return (status == 'CONNECT OK')
                assert Exception('The response exceeded expectations')
            except Exception as e:
                error = str(e)
                if(error == 'No reply'):
                    logger.warning('reset module ...')
                    raise Exception('reset module')
                elif(error == 'Failed'):
                    logger.warning('module response error, try again ...')
                else:
                    logger.error('Unknown exception: {}'.format(error))
                    raise Exception('Unknown exception')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    adapter = SerialAdapter('COM3')
    try:
        tcp = SIM7000E_TPC(adapter)
        mqtt_conn_pkg = '103A00044D51545404C2003C0020343937323132303436343637346563383861316166346137316436356237356600046D61707300066969736E726C'
        mqtt_publish_pkg_qos1 = '321C00174D4150532F4D415053362F423832374542354545344131000331'
        mqtt_publish_pkg_qos0 = '301A00174D4150532F4D415053362F42383237454235454534413138'
        tcp.connect('35.162.236.171', 8883)
        tcp.sendData(mqtt_conn_pkg)
        available_data_len = 0
        while(available_data_len == 0):
            available_data_len = tcp.available()
        print('mqtt connect receive data {} byte'.format(available_data_len))
        data = tcp.readData(4)
        print('mqtt connect receive data: {}'.format(data))

        tcp.sendData(mqtt_publish_pkg_qos1)
        available_data_len = 0
        while(available_data_len == 0):
            available_data_len = tcp.available()
        print('mqtt publish receive data {} byte'.format(available_data_len))
        data = tcp.readData(4)
        print('mqtt publish receive data: {}'.format(data))

        tcp.sendData(mqtt_publish_pkg_qos0)
        tcp.disconnect()
    except Exception as e:
        error = str(e)
        print(error)
