#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# sim7000E_TCP.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 4:03:34 PM

import logging
from sim_access.adapter import SerialAdapter
from sim_access.simcom import SIMModuleBase
from sim_access.ATCommands import ATCommands

logger = logging.getLogger(__name__)


class SIM7000E_TPC(SIMModuleBase):
    def __init__(self):
        pass

    def connect(self, ip, port):
        pass

    def disconnect(self):
        pass

    def sendData(self, data):
        pass

    def available(self):
        pass

    def readData(self, len):
        pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        # filename='SIM7000E.log',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    adapter = SerialAdapter('COM3')
    sim = SIM7000E_TPC(adapter)

    sim.network_attach()
    apn = sim.network_getapn()
    sim.network_setapn(apn)
    sim.network_bringup()
    addr = sim.network_ipaddr()
    print('My IP: {0}'.format(addr))
