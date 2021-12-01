#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mqtt.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 5:45:18 PM


import logging
import time

from sim_access.sim7000E_TCP import SIM7000E_TPC


logger = logging.getLogger(__name__)


class MQTT(SIM7000E_TPC):
    def __init__(self):
        self.keep_Alive_Interval = 60

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
                        # filename='SIM7000E.log',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    # adapter = SerialAdapter('COM3')
    # sim = SIM7000E_TPC(adapter)

    # sim.network_attach()
    # apn = sim.network_getapn()
    # sim.network_setapn(apn)
    # sim.network_bringup()
    # addr = sim.network_ipaddr()
    # print('My IP: {0}'.format(addr))

    # sim.mainloop()
