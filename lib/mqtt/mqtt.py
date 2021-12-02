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
from random import randint
import hashlib
from adapter import SerialAdapter
from sim7000E_TCP import SIM7000E_TPC


logger = logging.getLogger(__name__)


# byte 1, bits 7-0. Table 2.1 and 2.2
MQTT_CONTROL_TYPE_PACKET_CONNECT = '10'  # Client request to connect to Server
MQTT_CONTROL_TYPE_PACKET_CONNACK = '20'  # Connect acknowledgment
# FIXME: AND Table 2.2 - flag bits
MQTT_CONTROL_TYPE_PACKET_PUBLISH = '30'  # Publish message
MQTT_CONTROL_TYPE_PACKET_PUBACK = '40'   # Publish acknowledgment
# Publish re_TYPEceived (assured delivery part 1)
MQTT_CONTROL_TYPE_PACKET_PUBREC = '50'
# Publish release (assured delivery part 2)
MQTT_CONTROL_TYPE_PACKET_PUBREL = '62'
# Publish co_TYPEmplete (assured delivery part 3)
MQTT_CONTROL_TYPE_PACKET_PUBCOMP = '70'
MQTT_CONTROL_TYPE_PACKET_SUBSCRIBE = '82'  # Client subscribe request
MQTT_CONTROL_TYPE_PACKET_SUBACK = '90'  # Subscribe acknowledgment
MQTT_CONTROL_TYPE_PACKET_UNSUBSCRIBE = 'A2'  # Unsubscribe request
MQTT_CONTROL_TYPE_PACKET_UNSUBACK = 'B0'  # Unsubscribe acknowledgment
MQTT_CONTROL_TYPE_PACKET_PINGREQ = 'C0'  # PING request
MQTT_CONTROL_TYPE_PACKET_PINGRESP = 'D0'  # PING response
MQTT_CONTROL_TYPE_PACKET_DISCONNECT = 'E0'  # Client is disconnecting

MQTT_PROTOCOL_NAME = 'MQTT'
MQTT_PROTOCOL_LEVEL = '4'  # MQTT Version 3.1.1


class MQTT(SIM7000E_TPC):
    ''' Note: Remaining Length currently support range 0~16383(1~2 byte)
    '''

    def __init__(self, tcpSocket, broker, port=1883, username='', password='', keepAlive_s=300, mqtt_id='', clean_session=True):
        assert isinstance(tcp, SIM7000E_TPC)
        assert isinstance(broker, str)
        assert isinstance(port, int)
        assert isinstance(username, str)
        assert isinstance(password, str)
        assert isinstance(keepAlive_s, int)
        assert isinstance(mqtt_id, str)
        self.tcp = tcpSocket
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.keepAlive_s = keepAlive_s
        self.mqtt_id = mqtt_id
        self.clean_session = clean_session

    def connect(self):

        try:
            if(not self.tcp.connected()):
                self.tcp.connect(self.broker, self.port)
                # 3.1.1 Fixed header，xx = Remaining len
                packet = MQTT_CONTROL_TYPE_PACKET_CONNECT + 'XX'
                # 3.1.2.1 Protocol Name
                packet += str(len(MQTT_PROTOCOL_NAME)).zfill(4)
                packet += self.__strToHexString(MQTT_PROTOCOL_NAME)
                # 3.1.2.2 Protocol Level
                packet += str(MQTT_PROTOCOL_LEVEL).zfill(2)
                # 3.1.2.3 Connect Flags
                flag_bit = 0x00
                if(self.username):
                    # 3.1.2.8 User Name Flag
                    flag_bit |= 0x80
                if(self.password):
                    # 3.1.2.9 Password Flag
                    flag_bit |= 0x40
                # TODO: Add Will Retain(3.1.2.7)、Will QoS(3.1.2.6)、Will Flag(3.1.2.5)
                # 3.1.2.4 Clean Session
                flag_bit |= (self.clean_session << 1)
                packet += (hex(flag_bit)[2:].upper())
                # 3.1.2.10 Keep Alive
                packet += (hex(self.keepAlive_s)[2:].upper().zfill(4))
                # 3.1.3.1 Client Identifier
                # FIXME: [MQTT-3.1.3-9]
                if(not self.mqtt_id):
                    self.mqtt_id = hashlib.md5(
                        str(randint(0, 65535)).encode('utf-8')).hexdigest()
                packet += (hex(len(self.mqtt_id))[2:].upper().zfill(4))
                packet += self.__strToHexString(self.mqtt_id)
                # TODO: Add Will Topic(3.1.3.2)、Will Message(3.1.3.3)
                # 3.1.3.4 User Name
                if(self.username):
                    packet += (hex(len(self.username))[2:].upper().zfill(4))
                    packet += self.__strToHexString(self.username)
                if(self.password):
                    packet += (hex(len(self.password))[2:].upper().zfill(4))
                    packet += self.__strToHexString(self.password)
                # Replace the remaining length field
                remaining_len = int(len(packet[4:]) / 2)
                remaining = ''
                if(remaining_len > 0x7F):
                    byte1 = (int(remaining_len % 0x80) + 0x80)
                    byte2 = int(remaining_len / 0x80)
                    remaining = (hex(byte1)[2:].upper()) + \
                        (hex(byte2)[2:].upper().zfill(2))
                else:
                    remaining = hex(remaining_len)[2:].upper().zfill(2)
                packet = packet.replace('XX', remaining)
                logger.debug(packet)
        except Exception as e:
            error = str(e)

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

    def __strToHexString(string):
        return (''.join([hex(ord(x))[2:] for x in string])).upper()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    adapter = SerialAdapter('COM3')
    tcp = SIM7000E_TPC(adapter)

    broker = '35.162.236.171'
    port = 8883
    mqtt_id = 'B827EBDD70BA'
    keepAlive = 60
    username = 'maps'
    password = 'iisnrl'
    clear_session = True

    mqtt = MQTT(SIM7000E_TPC, broker, port, username,
                password, keepAlive, mqtt_id, clear_session)
    mqtt.connect()
