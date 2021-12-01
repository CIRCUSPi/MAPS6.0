#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mqtt.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 5:45:18 PM

import sys
sys.path.append('lib\\sim_access')

import logging
from adapter import SerialAdapter
from sim7000E_TCP import SIM7000E_TPC


logger = logging.getLogger(__name__)


class MQTT(SIM7000E_TPC):
    def __init__(self, tcpSocket):
        assert isinstance(tcp, SIM7000E_TPC)
        self.tcp = tcpSocket

    def connect(self, broker, port=1883, username="", password="", keepAlive=300, mqtt_id=""):
        pass

    def disconnect(self):
        pass

    def publish(self, topic, msg, qos=0):
        pass

    def subscribe(self, topic, qos=0):
        pass

    def unSubscribe(self, topic):
        pass

    def setCallback(self, function):
        pass

    def loop(self):
        pass

    def setKeepAliveInterval(self, keepAliveInterval):
        self.keep_Alive_Interval = keepAliveInterval


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    adapter = SerialAdapter('COM3')
    tcp = SIM7000E_TPC(adapter)
    mqtt = MQTT(SIM7000E_TPC)
