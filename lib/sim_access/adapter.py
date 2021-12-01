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


class MAPS6Adapter(AdapterBase):
    ''' MAPS6 Serial
    '''

    def __init__(self, COM, baud=115200):
        self.__port = serial.Serial(COM, baudrate=baud, timeout=2.0)

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
