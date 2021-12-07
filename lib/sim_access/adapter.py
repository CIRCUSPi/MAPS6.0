#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# adapter.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 9:49:38 AM

import sys
sys.path.append('lib\\sim_access')

import six
import serial
from abc import ABCMeta, abstractmethod
import logging
import time


logger = logging.getLogger(__name__)


@six.add_metaclass(ABCMeta)
class AdapterBase(object):

    @abstractmethod
    def read(self, size=0):
        raise NotImplementedError()

    @abstractmethod
    def readline(self):
        raise NotImplementedError()

    @abstractmethod
    def write(self, data):
        raise NotImplementedError()

    @abstractmethod
    def available(self):
        raise NotImplementedError()


class SerialAdapter(AdapterBase):
    ''' Python Serial
    '''

    def __init__(self, COM, baud=115200):
        self.__port = serial.Serial(COM, baudrate=baud, timeout=0.05)

    def read(self, size=0):
        if size == 0:
            data = self.__port.read_all()
        else:
            data = self.__port.read(size)
        return data

    def readline(self):
        data = self.__port.readline()
        logger.debug('<' + data.decode())
        return data

    def write(self, data):
        assert isinstance(data, bytes)
        logger.debug('>' + data.decode())
        self.__port.write(data)

    def available(self):
        return self.__port.in_waiting


MAPS_NBIOT_UART_PORT = 0x00
LEADING_CMD = 0xAA
MAPS_UART_BEGIN_CMD = 0xCC
MAPS_UART_ENABLE_ACTIVE_RX_CMD = 0xCF
MAPS_UART_TX_RX_CMD = 0xCD
MAPS_UART_TXRX_EX_CMD = 0xCE


class MAPS6Adapter(AdapterBase):
    ''' MAPS6 Serial
    '''

    def __init__(self, COM, baud=115200):
        self.__port = serial.Serial(COM, baudrate=baud, timeout=0.05)
        self.__buffer = bytearray()
        self.__Written_flag = False
        self.write(self.__Make_PROTOCOL_UART_BEGIN_CMD())
        self.write(self.__Make_ENABLE_UART_ACTIVE_RX_CMD(
            MAPS_NBIOT_UART_PORT, True, 100, 50, 10000))

    def __Not(self, byte):
        return ~byte & 0xFF

    def __Calc_checkSum(self, datas):
        return (sum([(data) ^ ((idx + 1) % 0x100) for idx, data in enumerate(datas)]) & 0xFF)

    def __int16_to_2byte(num):
        return [num & 0xFF, (num >> 8) & 0xFF]

    def __int32_to_4byte(num):
        return [num & 0xFF, (num >> 8) & 0xFF, (num >> 16) & 0xFF, (num >> 24) & 0xFF]

    def __Make_ENABLE_UART_ACTIVE_RX_CMD(self, port, enable, polling_time, byte_timeout, rcv_timeout):
        data = bytearray()
        data.append(LEADING_CMD)
        data.append(self.__Not(LEADING_CMD))
        data.append(MAPS_UART_ENABLE_ACTIVE_RX_CMD)
        data.append(self.__Not(MAPS_UART_ENABLE_ACTIVE_RX_CMD))
        data.append(port)
        data.append(enable)
        data.append(polling_time)
        data.append(byte_timeout)
        data.extend(self.__int16_to_2byte(rcv_timeout))
        checksum = self.__Calc_checkSum(data)
        data.append(checksum)
        data.append(self.__Not(checksum))
        return bytes(data)

    def __Make_PROTOCOL_UART_TX_CMD(self, port, cmd):
        data = bytearray()
        data.append(LEADING_CMD)
        data.append(self.__Not(LEADING_CMD))
        data.append(MAPS_UART_TX_RX_CMD)
        data.append(self.__Not(MAPS_UART_TX_RX_CMD))
        data.append(port)
        data.extend(self.__int16_to_2byte(len(cmd)))
        data.extend(self.__int16_to_2byte(0))
        data.extend(self.__int32_to_4byte(0))
        data.extend(cmd)
        checksum = self.__Calc_checkSum(data)
        data.append(checksum)
        data.append(self.__Not(checksum))
        return bytes(data)

    def __Make_PROTOCOL_UART_TXRX_EX_CMD(self, port, cmd, byte_timeout, wait_timeout):
        data = bytearray()
        data.append(LEADING_CMD)
        data.append(self.__Not(LEADING_CMD))
        data.append(MAPS_UART_TXRX_EX_CMD)
        data.append(self.__Not(MAPS_UART_TXRX_EX_CMD))
        data.append(port)
        data.extend(self.__int16_to_2byte(len(cmd)))
        data.append(byte_timeout)
        data.extend(self.__int32_to_4byte(wait_timeout))
        data.extend(cmd)
        checksum = self.__Calc_checkSum(data)
        data.append(checksum)
        data.append(self.__Not(checksum))
        return bytes(data)

    def __Make_PROTOCOL_UART_BEGIN_CMD(self):
        data = bytearray()
        data.append(LEADING_CMD)
        data.append(self.__Not(LEADING_CMD))
        data.append(MAPS_UART_BEGIN_CMD)
        data.append(self.__Not(MAPS_UART_BEGIN_CMD))
        data.append(0x00)
        data.append(0x04)
        data.append(0x00)
        checksum = self.__Calc_checkSum(data)
        data.append(checksum)
        data.append(self.__Not(checksum))
        return bytes(data)

    def __receive_maps_data(self):
        pass

    def read(self, size=0):
        pass

    def readline(self):
        pass

    def write(self, data):
        assert isinstance(data, bytes)
        logger.debug('>' + data.decode())
        self.__port.write(self.__Make_PROTOCOL_UART_TX_CMD(
            MAPS_NBIOT_UART_PORT, data))

        timeout = time.time() + 2.0
        while(not self.__Written_flag and time.time() < timeout):
            self.__receive_maps_data()
        self.__Written_flag = False

    def available(self):
        pass
