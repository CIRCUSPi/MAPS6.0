#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mian.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 12/15/2021, 11:43:57 AM

import serial
from time import sleep, perf_counter
import logging
from datetime import datetime
import requests
import os
from enum import Enum
import threading
from os import listdir


from libs.MEGA2560 import mega2560
from libs.MEGA2560.mega2560 import Mega2560
from libs.SIM7000E.sim_access.adapter import MAPS6Adapter
from libs.SIM7000E.sim_access.sim7000E_TCP import SIM7000E_TPC
from libs.SIM7000E.mqtt.mqtt import MQTT
from libs.SSD1306.ssd1306 import SSD1306

logger = logging.getLogger('maps6')
logging.basicConfig(
    # filename='maps6.log',
    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
logger.setLevel(logging.DEBUG)


class ConnectionState(Enum):
    NAN = 0
    WIFI = 1
    NBIOT = 2


# global variable
UPLOAD_INTERVAL = 300  # second
GET_SENSOR_DATA_INTERVAL = 5  # second
CHECK_WIFI_INTERVAL = 10  # second
SAVE_SD_INTERVAL = 60  # second

# Device config
DEVIDE_ID = open(
    '/sys/class/net/eth0/address').readline().upper().strip().replace(':', '')
MAPS_PI_VERSION = '7.0.0'
APP_ID = 'MAPS6'

# HTTPS config (WiFi)
LASS_REST_URL = 'https://data.lass-net.org/Upload/MAPS-secure.php'

# MQTT config (NBIoT)
BROKER = '35.162.236.171'
MQTT_PORT = 8883
MQTT_ID = DEVIDE_ID
KEEPALIVE = 270
USERNAME = 'maps'
PASSWORD = 'iisnrl'
CLEAR_SESSION = True

TOPIC = f'MAPS/MAPS6/{MQTT_ID}'
QOS = 1

sensor_data = None
connectionState = ConnectionState.NAN
nbiot_csq = '-'

nbiot_detected = False


def save_sd_task():
    global sensor_data

    while(True):
        sleep(SAVE_SD_INTERVAL)
        time_pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(' ')
        # check is SD card is on the board
        if os.path.exists("/dev/mmcblk2p1"):
            logger.info("SD exists")
            sd = listdir('/media/pi/')
            if(len(sd) > 0):
                data_list = [DEVIDE_ID, time_pairs[0], time_pairs[1], sensor_data['TEMP'], sensor_data['HUMI'], sensor_data['PM2.5_AE'],
                             sensor_data['PM1.0_AE'], sensor_data['PM10.0_AE'], sensor_data['Illuminance'], sensor_data['CO2'],  sensor_data['TVOC']]
                data = ','.join([str(d) for d in data_list])
                try:
                    with open(f'/media/pi/{sd[0]}/{time_pairs[0]}.csv', 'a+') as f:
                        f.write(f'{data}\n')
                    logger.info('Save sensor data to SD Card.')
                except Exception as e:
                    logger.error(e)
        else:
            logger.info("NO SD card")


def NBIoT_publish_to_lass(m_mqtt):
    global sensor_data

    pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(' ')
    msg = f"|gps_lon={0}|gps_lat={0}|s_g8={sensor_data['CO2']}|s_t0={sensor_data['TEMP']}|app={APP_ID}|date={pairs[0]}|s_d0={sensor_data['PM2.5_AE']}|s_h0={sensor_data['HUMI']}|device_id={DEVIDE_ID}|s_gg={sensor_data['TVOC']}|ver_app={MAPS_PI_VERSION}|time={pairs[1]}|MQ"
    logger.info(f'publish message: {msg}')
    return m_mqtt.publish(TOPIC, msg, QOS)


def oled_task():
    global nbiot_csq
    global sensor_data

    oled = SSD1306()
    while True:
        internet_icon = '-'
        if(connectionState == ConnectionState.WIFI):
            internet_icon = 'W'
            nbiot_csq = '-'
        elif(connectionState == ConnectionState.NBIOT):
            internet_icon = 'N'
        oled.display(DEVIDE_ID, sensor_data['TEMP'], sensor_data['HUMI'], sensor_data['PM2.5_AE'], sensor_data['CO2'],
                     sensor_data['TVOC'], internet_icon, MAPS_PI_VERSION, nbiot_csq)
        sleep(0.3)


def wifi_upload_to_lass():
    global sensor_data

    pairs = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S").split(' ')
    msg = f"|gps_lon={0}|gps_lat={0}|s_g8={sensor_data['CO2']}|s_t0={sensor_data['TEMP']}|app={APP_ID}|date={pairs[0]}|s_d0={sensor_data['PM2.5_AE']}|s_h0={sensor_data['HUMI']}|device_id={DEVIDE_ID}|s_gg={sensor_data['TVOC']}|ver_app={MAPS_PI_VERSION}|time={pairs[1]}|MQ"
    logger.info(f'upload message: {msg}')

    get_api = f'{LASS_REST_URL}?topic={APP_ID}&device_id={DEVIDE_ID}&key=NoKey&msg={msg}'
    try:
        result = requests.get(get_api)
        logger.info(f'HTTPS Get Result: {result}')
    except Exception as e:
        logger.error(e)


def check_connection(sim7000e_tcp):
    global connectionState
    global nbiot_detected

    if(not os.system('ping www.google.com -q -c 1  > /dev/null')):
        connectionState = ConnectionState.WIFI
    elif(nbiot_detected and sim7000e_tcp.network_chkAttach()):
        connectionState = ConnectionState.NBIOT
    else:
        connectionState = ConnectionState.NAN
    logger.info(f'connectionState: {connectionState}')


def check_gps_csq(sim7000e_tcp):
    global nbiot_csq
    global nbiot_detected

    if(not nbiot_detected):
        return
    if(sim7000e_tcp.network_chkAttach()):
        nbiot_csq = sim7000e_tcp.network_getCsq()
    gps_info = sim7000e_tcp.get_gps_info()
    logger.debug(gps_info)


if __name__ == '__main__':
    m_serial = serial.Serial('/dev/ttyAMA0', baudrate=115200, timeout=0.05)

    logger.info(f'UPLOAD_INTERVAL: {UPLOAD_INTERVAL}')
    logger.info(f'GET_SENSOR_DATA_INTERVAL: {GET_SENSOR_DATA_INTERVAL}')
    logger.info(f'CHECK_WIFI_INTERVAL: {CHECK_WIFI_INTERVAL}')
    logger.info(f'DEVIDE_ID: {DEVIDE_ID}')
    logger.info(f'MAPS_PI_VERSION: {MAPS_PI_VERSION}')
    logger.info(f'RPI_APP_ID: {APP_ID}')
    logger.info(f'LASS_REST_URL: {LASS_REST_URL}')
    logger.info(f'MQTT BROKER: {BROKER}')
    logger.info(f'MQTT_PORT: {MQTT_PORT}')
    logger.info(f'MQTT_ID: {MQTT_ID}')
    logger.info(f'MQTT KEEPALIVE: {KEEPALIVE}')
    logger.info(f'MQTT USERNAME: {USERNAME}')
    logger.info(f'MQTT PASSWORD: {PASSWORD}')
    logger.info(f'MQTT CLEAR_SESSION: {CLEAR_SESSION}')
    logger.info(f'MQTT TOPIC: {TOPIC}')
    logger.info(f'MQTT Publish QOS: {QOS}')
    # wait MAPS Boot up
    sleep(5)

    m_adapter = MAPS6Adapter(m_serial)  # UART bridge
    m_mega2560 = Mega2560(m_serial)  # Sensor, RTC, polling error count

    m_sim7000e_tcp = None
    m_mqtt = None

    try:
        m_sim7000e_tcp = SIM7000E_TPC(m_adapter)  # SIM7000E TCP Command
        m_mqtt = MQTT(m_sim7000e_tcp, BROKER, MQTT_PORT, USERNAME,
                      PASSWORD, KEEPALIVE, MQTT_ID, CLEAR_SESSION)
        nbiot_detected = True
    except Exception as e:
        error = str(e)
        if(error == 'No module or SIM card'):
            logger.info('SIM7000E not detected.')

    m_mega2560.set_sensor_all_polling()

    publish_timer = perf_counter() + UPLOAD_INTERVAL
    get_sensor_timer = 0
    check_wifi_timer = 0

    oled_task_t = threading.Thread(target=oled_task, name="oled_task_t")
    oled_task_t.setDaemon(True)

    save_sd_task_t = threading.Thread(
        target=save_sd_task, name="save_sd_task_t")
    save_sd_task_t.setDaemon(True)

    oled_task_t.start()
    save_sd_task_t.start()

    while(True):
        try:
            if(perf_counter() > publish_timer):
                publish_timer = perf_counter() + UPLOAD_INTERVAL
                result = None
                if(connectionState == ConnectionState.WIFI):  # using WiFi
                    result = wifi_upload_to_lass()
                    if(m_mqtt.connected()):
                        m_mqtt.disconnect()
                elif(connectionState == ConnectionState.NBIOT):  # using NBIoT
                    if(not m_mqtt.connected()):
                        logger.info(
                            f'm_mqtt disconnect result: {m_mqtt.disconnect()}')
                        logger.info(
                            f'm_mqtt connect result: {m_mqtt.connect()}')
                    result = NBIoT_publish_to_lass(m_mqtt)
                else:
                    logger.info(
                        'There is no valid network, please check if you can connect to WiFi or NB-IoT')
                logger.info(f'upload_to_lass result: {result}')

            # Get All Sensor Data
            if(perf_counter() > get_sensor_timer):
                get_sensor_timer = perf_counter() + GET_SENSOR_DATA_INTERVAL
                sensor_data = m_mega2560.get_sensor_all()
                if(sensor_data['CO2'] == 65535):
                    sensor_data['CO2'] = -1
                logger.info(sensor_data)

            # Check WiFi valid
            if(perf_counter() > check_wifi_timer):
                check_wifi_timer = perf_counter() + CHECK_WIFI_INTERVAL
                check_connection(m_sim7000e_tcp)
        except Exception as e:
            logger.error(e)
        sleep(0.01)
