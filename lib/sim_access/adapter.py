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
        return self.__port.read_all() if size == 0 else self.__port.read(size)

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
MAPS_LEADING_CMD = 0xAA
MAPS_UART_BEGIN_CMD = 0xCC
MAPS_UART_ENABLE_ACTIVE_RX_CMD = 0xCF
MAPS_UART_TX_RX_CMD = 0xCD
MAPS_UART_TXRX_EX_CMD = 0xCE
MAPS_ECHO_UART_ACTIVE_RX_CMD = 0xD0


class ByteFIFO(object):
    """ byte FIFO buffer """

    def __init__(self):
        self.__buf = bytearray()

    def put(self, data):
        self.__buf.extend(data)

    def get(self, size):
        data = self.__buf[:size]
        # The fast delete syntax
        self.__buf[:size] = b''
        return data

    def peek(self, size):
        return self.__buf[:size]

    def getvalue(self):
        # peek with no copy
        return bytes(self.__buf)

    def readline(self):
        end_idx = self.__buf.find(0x0A)
        if(end_idx != -1):
            return bytes(self.get(end_idx + 1))
        return bytes(self.get(self._len()))

    def _len(self):
        return len(self.__buf)


class MAPS6Adapter(AdapterBase):
    ''' MAPS6 Serial
    '''

    def __init__(self, COM, baud=115200):
        self.__port = serial.Serial(COM, baudrate=baud, timeout=0.05)
        time.sleep(2)
        self.__buffer_FIFO = ByteFIFO()
        self.__port.write(self.__Make_PROTOCOL_UART_BEGIN_CMD())
        self.__wait_response(MAPS_UART_BEGIN_CMD)
        self.__port.write(self.__Make_ENABLE_UART_ACTIVE_RX_CMD(
            MAPS_NBIOT_UART_PORT, True, 100, 50, 10000))
        self.__wait_response(MAPS_UART_ENABLE_ACTIVE_RX_CMD)

    def __Not(self, byte):
        return ~byte & 0xFF

    def __Calc_checkSum(self, datas):
        return (sum([(data) ^ ((idx + 1) % 0x100) for idx, data in enumerate(datas)]) & 0xFF)

    def __int16_to_2byte(self, num):
        return [num & 0xFF, (num >> 8) & 0xFF]

    def __int32_to_4byte(self, num):
        return [num & 0xFF, (num >> 8) & 0xFF, (num >> 16) & 0xFF, (num >> 24) & 0xFF]

    def __Make_ENABLE_UART_ACTIVE_RX_CMD(self, port, enable, polling_time, byte_timeout, rcv_timeout):
        data = bytearray()
        data.append(MAPS_LEADING_CMD)
        data.append(self.__Not(MAPS_LEADING_CMD))
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
        data.append(MAPS_LEADING_CMD)
        data.append(self.__Not(MAPS_LEADING_CMD))
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
        data.append(MAPS_LEADING_CMD)
        data.append(self.__Not(MAPS_LEADING_CMD))
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
        data.append(MAPS_LEADING_CMD)
        data.append(self.__Not(MAPS_LEADING_CMD))
        data.append(MAPS_UART_BEGIN_CMD)
        data.append(self.__Not(MAPS_UART_BEGIN_CMD))
        data.append(0x00)
        data.append(0x04)
        data.append(0x00)
        checksum = self.__Calc_checkSum(data)
        data.append(checksum)
        data.append(self.__Not(checksum))
        return bytes(data)

    def __wait_response(self, response_cmd=0x00, timeout=1000):
        timeout = time.time() + (timeout / 1000)
        while(time.time() < timeout):
            while(self.__port.inWaiting() >= 2):
                bytes_data = self.__port.read(2)
                if(bytes_data[0] == MAPS_LEADING_CMD and bytes_data[1] == response_cmd):
                    bytes_data = self.__port.read(2)
                    return (bytes_data[0] == 0x00 and bytes_data[1] == 0xFF)
                elif(bytes_data[0] == MAPS_LEADING_CMD and bytes_data[1] == MAPS_ECHO_UART_ACTIVE_RX_CMD):
                    if(not self.__receive_maps_echo(bytes_data)):
                        logger.debug(f'Maps Echo: False')
        return False

    def __receive_maps_echo(self, bytes_header):
        uart_port = self.__port.read(1)
        if(uart_port[0] != MAPS_NBIOT_UART_PORT):
            self.__port.read_all()
            return False
        rx_length_k = self.__port.read(2)
        rcv_len = (rx_length_k[0] | (rx_length_k[1] << 8))
        if(rcv_len < 1 or rcv_len > 2048):
            self.__port.read_all()
            return False
        module_data = self.__port.read(rcv_len)
        if(len(module_data) != rcv_len):
            self.__port.read_all()
            return False
        all_data = bytearray()
        all_data.extend(bytes_header)
        all_data.extend(uart_port)
        all_data.extend(rx_length_k)
        all_data.extend(module_data)
        checksum = self.__Calc_checkSum(all_data)
        rcv_checksums = self.__port.read(2)
        if (rcv_checksums[0] != checksum or rcv_checksums[1] != self.__Not(checksum)):
            self.__port.read_all()
            return False
        self.__buffer_FIFO.put(module_data)
        return True

    def read(self, size=0):
        self.__wait_response(timeout=50)
        if(size == 0):
            data = self.__buffer_FIFO.get(self.__buffer_FIFO._len())
        else:
            data = self.__buffer_FIFO.get(size)
        return data

    def readline(self, timeout=50):
        self.__wait_response(timeout=timeout)
        data = self.__buffer_FIFO.readline()
        logger.debug('<' + data.decode())
        return data

    def write(self, data):
        assert isinstance(data, bytes)
        logger.debug('>' + data.decode())
        try_count = 0
        while(try_count < 10):
            self.__port.write(self.__Make_PROTOCOL_UART_TX_CMD(
                MAPS_NBIOT_UART_PORT, data))
            if(self.__wait_response(MAPS_UART_TX_RX_CMD)):
                break
            logger.info('write error, try again...')
            try_count += 1
            time.sleep(1)

    def available(self):
        pass
