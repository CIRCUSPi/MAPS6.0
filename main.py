#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# main.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 12/1/2021, 5:07:51 PM

import logging
import time

from lib.sim_access.adapter import SerialAdapter, MAPS6Adapter
from lib.sim_access.sim7000E_TCP import SIM7000E_TPC
from lib.mqtt.mqtt import MQTT

logger = logging.getLogger(__name__)

receive_count = 0


def callback(topic, msg):
    global receive_count
    logger.info('Topic: {}, Msg: {}'.format(topic, msg))
    receive_count += 1
    print(f'receive_count: {receive_count}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        filename='maps6.log',
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    adapter = MAPS6Adapter('COM8')
    tcp = SIM7000E_TPC(adapter)

    broker = '35.162.236.171'
    port = 8883
    mqtt_id = 'B827EBDD70BA_2'
    keepAlive = 270
    username = 'maps'
    password = 'iisnrl'
    clear_session = True

    topic = 'MAPS/MAPS6/B827EB5EE4A1'
    msg = 'Hello word !'
    qos = 1

    mqtt = MQTT(tcp, broker, port, username,
                password, keepAlive, mqtt_id, clear_session)
    mqtt.disconnect()
    if(mqtt.connect()):
        print('MQTT Connect success')
        # print('Subscribe qos: {}'.format(mqtt.subscribe(topic, qos)))
        print('Publish result: {}'.format(
            mqtt.publish(topic, msg, qos)))
        # print('unSubscribe result: {}'.format(mqtt.unSubscribe(topic)))
        print('PingReq result: {}'.format(mqtt.pingReq()))
        test_timer = time.time()
        chk_conn_timer = time.time()
        pub_count = 0
        pub_count_success = 0
        while(True):
            try:
                if(time.time() > test_timer):
                    cur_time = time.time()
                    test_timer = cur_time + 300
                    pub_msg = 'PC: ' + str(cur_time)
                    pub_result = mqtt.publish(topic, pub_msg, qos)
                    pub_count += 1
                    print(f'Publish {pub_msg}, result: {pub_result}')
                    if(pub_result):
                        pub_count_success += 1
                    print(
                        f'pub_count: {pub_count}, success count: {pub_count_success}, csq: {tcp.network_getCsq()}')
                mqtt.loop()
                if(time.time() > chk_conn_timer):
                    chk_conn_timer = time.time() + 5
                    if(not mqtt.connected()):
                        mqtt.disconnect()
                        mqtt.connect()
            except Exception as e:
                print(e)
    else:
        print('MQTT Connect fail')
