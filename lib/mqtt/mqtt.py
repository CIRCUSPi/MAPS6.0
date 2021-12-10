#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mqtt.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 5:45:18 PM

import re

import logging
import time
from random import randint
import hashlib
import re
from lib.sim_access.adapter import SerialAdapter, MAPS6Adapter
from lib.sim_access.sim7000E_TCP import SIM7000E_TPC


logger = logging.getLogger(__name__)


# byte 1, bits 7-0. Table 2.1 and 2.2
MQTT_CONTROL_TYPE_PACKET_CONNECT = '10'  # Client request to connect to Server
MQTT_CONTROL_TYPE_PACKET_CONNACK = '20'  # Connect acknowledgment
# FIXME: AND Table 2.2 - flag bits
MQTT_CONTROL_TYPE_PACKET_PUBLISH = '3'  # Publish message
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


class MQTT(object):
    ''' Note: Remaining Length currently support range 0~16383(1~2 byte).
        Note: QoS currently support range 0~1.
        Note: All exceptions are handled in the MQTT category.
    '''

    def __init__(self, tcpSocket, broker, port=1883, username='', password='', keepAlive_s=300, mqtt_id='', clean_session=True):
        assert isinstance(tcpSocket, SIM7000E_TPC)
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
        self.publish_qos1_count = 0
        self.callback = None
        self.buffer = []
        self.pingReq_timer = time.time() + self.keepAlive_s

    def connect(self):
        ''' 3.1 CONNECT - Client requests a connection to a Server
        '''
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
                packet = packet.replace(
                    'XX', self.__calcRemainingLen(remaining_len))
                logger.debug(packet)
                self.tcp.sendData(packet)
                # Wait Response
                # 3.2 CONNACK - Acknowledge connection request
                if(self.__waitResponse(MQTT_CONTROL_TYPE_PACKET_CONNACK + '02')):
                    # 3.2.1 Fixed header
                    # 3.2.2 Variable header
                    receive_packet = self.tcp.readData(2)
                    if(int(len(receive_packet) / 2) == 2):
                        byte1 = receive_packet[:2]
                        byte2 = receive_packet[2:4]
                        if(byte1 == '01'):
                            logger.warning(
                                'Server has stored 684 Session state')
                        if(byte2 == '00'):
                            logger.info('MQTT Connection Accepted.')
                            return True
                        elif(byte2 == '01'):
                            logger.warning(
                                'MQTT Connection Refused, unacceptable protocol version')
                        elif(byte2 == '02'):
                            logger.warning(
                                'MQTT Connection Refused, identifier rejected')
                        elif(byte2 == '03'):
                            logger.warning(
                                'MQTT Connection Refused, Server unavailable')
                        elif(byte2 == '04'):
                            logger.warning(
                                'MQTT Connection Refused, bad user name or password')
                        elif(byte2 == '05'):
                            logger.warning(
                                'MQTT Connection Refused, not authorized')
                        return False
                    else:
                        raise Exception(
                            'receive_packet >> The length is not 2 bytes')
                else:
                    raise Exception(
                        'receive_packet >> The beginning does not match 2002')
        except Exception as e:
            error = str(e)
            logger.error(error)
            return False

    def disconnect(self):
        ''' 3.14 DISCONNECT - Disconnect notification
        '''
        # 3.14.1 Fixed header
        try:
            packet = MQTT_CONTROL_TYPE_PACKET_DISCONNECT + '00'
            logger.debug(packet)
            try:
                if(self.tcp.connected()):
                    self.tcp.sendData(packet)
            except Exception as e:
                logger.warning('MQTT Disconnect send packet error.')
            time.sleep(0.5)
            self.tcp.disconnect()
            logger.info('MQTT Disconnected.')
            return True
        except Exception as e:
            error = str(e)
            logger.error(error)
            return False

    def publish(self, topic, msg, qos=0, retain=False):
        assert isinstance(topic, str)
        assert isinstance(msg, str)
        assert isinstance(qos, int)
        assert isinstance(retain, bool)
        assert (qos >= 0 and qos <= 1)
        try:
            if(self.tcp.connected()):
                # TODO: 3.3.1.1 DUP
                # 3.3.1.2 QoS
                flag_bits = 0x00 | (qos << 1)
                flag_bits |= retain
                packet = MQTT_CONTROL_TYPE_PACKET_PUBLISH + \
                    hex(flag_bits)[2:].upper() + 'XX'
                # 3.3.2.1 Topic Name
                packet += (hex(len(topic))[2:].upper().zfill(4))
                packet += self.__strToHexString(topic)
                # 3.3.2.2 Packet Identifier
                send_identifier = ''
                if(qos == 1):
                    self.publish_qos1_count += 1
                    self.publish_qos1_count %= 0xFFFF
                    send_identifier = (hex(self.publish_qos1_count)[
                        2:].upper().zfill(4))
                    packet += send_identifier
                # 3.3.3 Payload
                packet += self.__strToHexString(msg)
                # Replace the remaining length field
                remaining_len = int(len(packet[4:]) / 2)
                packet = packet.replace(
                    'XX', self.__calcRemainingLen(remaining_len))
                logger.debug(packet)
                self.tcp.sendData(packet)
                if(qos == 0):
                    return True
                # Wait Response
                # 3.4 PUBACK - Publish acknowledgement
                if(self.__waitResponse(MQTT_CONTROL_TYPE_PACKET_PUBACK + '02')):
                    # 3.4.1 Fixed header
                    receive_packet = self.tcp.readData(2)
                    if(int(len(receive_packet) / 2) == 2):
                        # 3.4.2 Variable header
                        receive_identifier = receive_packet
                        if(receive_identifier == send_identifier):
                            return True
            else:
                logger.info('MQTT not connected.')
            return False
        except Exception as e:
            error = str(e)
            logger.error(error)
            return False

    def subscribe(self, topic, qos=0):
        ''' 3.8 SUBSCRIBE - Subscribe to topics
            return qos
        '''
        assert isinstance(topic, str)
        assert isinstance(qos, int)
        assert (qos >= 0 and qos <= 1)
        try:
            if(self.tcp.connected()):
                # 3.8.1 Fixed header
                packet = MQTT_CONTROL_TYPE_PACKET_SUBSCRIBE + 'XX'
                # 3.8.2 Variable header
                send_identifier = (hex(randint(0, 65535))[2:].upper().zfill(4))
                packet += send_identifier
                # 3.8.3 Payload
                packet += (hex(len(topic))[2:].upper().zfill(4))
                packet += self.__strToHexString(topic)
                packet += str(qos).zfill(2)
                # Replace the remaining length field
                remaining_len = int(len(packet[4:]) / 2)
                packet = packet.replace(
                    'XX', self.__calcRemainingLen(remaining_len))
                logger.debug(packet)
                self.tcp.sendData(packet)
                # Wait Response
                # 3.9 SUBACK - Subscribe acknowledgement
                if(self.__waitResponse(MQTT_CONTROL_TYPE_PACKET_SUBACK + '03')):
                    # 3.9.1 Fixed header
                    receive_packet = self.tcp.readData(3)
                    if(int(len(receive_packet) / 2) == 3):
                        # 3.9.2 Variable header
                        receive_identifier = receive_packet[:4]
                        if(receive_identifier == send_identifier):
                            receive_qos = receive_packet[4:6]
                            if(receive_qos == '80'):
                                return None
                            elif(receive_qos == '00' or receive_qos == '01'):
                                return int(receive_qos)
            else:
                logger.info('MQTT not connected.')
            return None
        except Exception as e:
            error = str(e)
            logger.error(error)
            return None

    def unSubscribe(self, topic):
        ''' 3.10 UNSUBSCRIBE - Unsubscribe from topics
        '''
        assert isinstance(topic, str)
        try:
            if(self.tcp.connected()):
                # 3.10.1 Fixed header
                packet = MQTT_CONTROL_TYPE_PACKET_UNSUBSCRIBE + 'XX'
                # 3.10.2 Variable header
                send_identifier = (hex(randint(0, 65535))[2:].upper().zfill(4))
                packet += send_identifier
                # 3.10.3 Payload
                packet += (hex(len(topic))[2:].upper().zfill(4))
                packet += self.__strToHexString(topic)
                # Replace the remaining length field
                remaining_len = int(len(packet[4:]) / 2)
                packet = packet.replace(
                    'XX', self.__calcRemainingLen(remaining_len))
                logger.debug(packet)
                self.tcp.sendData(packet)
                # Wait Response
                # 3.11 UNSUBACK - Unsubscribe acknowledgement
                if(self.__waitResponse(MQTT_CONTROL_TYPE_PACKET_UNSUBACK + '02')):
                    # 3.11.1 Fixed header
                    receive_packet = self.tcp.readData(2)
                    if(int(len(receive_packet) / 2) == 2):
                        # 3.11.2 Variable header
                        receive_identifier = receive_packet
                        if(receive_identifier == send_identifier):
                            return True
            else:
                logger.info('MQTT not connected.')
            return False
        except Exception as e:
            error = str(e)
            logger.error(error)
            return False

    def pingReq(self):
        ''' 3.12 PINGREQ - PING request
        '''
        try:
            if(self.tcp.connected()):
                # 3.12.1 Fixed header
                packet = MQTT_CONTROL_TYPE_PACKET_PINGREQ + '00'
                logger.debug(packet)
                self.tcp.sendData(packet)
                logger.info('pingReq')
                # Wait Response
                # 3.13 PINGRESP - PING response
                return (self.__waitResponse(MQTT_CONTROL_TYPE_PACKET_PINGRESP + '00'))
            else:
                logger.info('MQTT not connected.')
            return False
        except Exception as e:
            error = str(e)
            logger.error(error)
            return False

    def connected(self):
        try:
            return self.tcp.connected()
        except Exception as e:
            error = str(e)
            logger.error(error)
            return False

    def setCallback(self, callback):
        self.callback = callback

    def loop(self):
        try:
            if(time.time() > self.pingReq_timer):
                self.pingReq_timer = time.time() + self.keepAlive_s
                if(not self.pingReq()):
                    logger.info(
                        'Not receive ping response, TCP Disconnecting...')
                    self.disconnect()
            # FIXME: 暫不處理MQTT被動收到的資料
            # Handle temp buffer
            # self.__waitResponse('', 50)
            # while(len(self.buffer) > 0):
            #     buff = self.buffer[0]
            #     topic_len = int(buff[1][:4], 16)
            #     topic_end_idx = 4 + (topic_len * 2)
            #     topic = self.__hexStrToStr(buff[1][4:topic_end_idx])
            #     # Qos
            #     if(buff[0] == 1):
            #         identifier = int(buff[1][topic_end_idx:topic_end_idx + 4], 16)
            #         topic_end_idx += 4
            #     msg = self.__hexStrToStr(buff[1][topic_end_idx:])
            #     self.callback(topic, msg)
            #     self.buffer = self.buffer[1:]
            return True
        except Exception as e:
            error = str(e)
            logger.error(error)
            return False

    def setKeepAliveInterval(self, keepAliveInterval):
        self.keepAlive_s = keepAliveInterval

    def __strToHexString(self, string):
        return (''.join([hex(ord(x))[2:] for x in string])).upper()

    def __hexStrToStr(self, hexStr):
        hex_byte_s = re.findall(r'.{2}', hexStr)
        return (''.join(chr(int(hex_byte, 16)) for hex_byte in hex_byte_s))

    def __calcRemainingLen(self, remaining_len):
        if(remaining_len > 0x7F):
            byte1 = (int(remaining_len % 0x80) + 0x80)
            byte2 = int(remaining_len / 0x80)
            return (hex(byte1)[2:].upper()) + \
                (hex(byte2)[2:].upper().zfill(2))
        else:
            return hex(remaining_len)[2:].upper().zfill(2)

    def __waitResponse(self, packet_header, timeout=120000):
        # FIXME: There may be bugs here...
        m_timeout = time.time() + (timeout / 1000)
        while(time.time() < m_timeout):
            if(self.tcp.available() >= 2):
                receive_packet = self.tcp.readData(2)
                if(receive_packet == packet_header):
                    return True
                elif(receive_packet[:2] == '30' or receive_packet[:2] == '32'):
                    qos = (int(receive_packet[1:2], 16) >> 1)
                    # Save data publish from the broker
                    if(self.tcp.available()):
                        remaining_len = int(receive_packet[2:4], 16)
                        # FIXME: 暫不儲存MQTT被動收到的資料
                        # self.buffer.append(
                        #     [qos, self.tcp.readData(remaining_len)])
                        m_timeout = time.time() + (timeout / 1000)
                else:
                    logger.error(
                        'Unprocessable packet: {}'.format(receive_packet))
        return False


if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    adapter = MAPS6Adapter('COM8')
    tcp = SIM7000E_TPC(adapter)

    broker = '35.162.236.171'
    port = 8883
    mqtt_id = 'B827EBDD70BA'
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
        print('Subscribe qos: {}'.format(mqtt.subscribe(topic, qos)))
        print('Publish result: {}'.format(
            mqtt.publish(topic, msg, qos)))
        print('unSubscribe result: {}'.format(mqtt.unSubscribe(topic)))
        print('PingReq result: {}'.format(mqtt.pingReq()))
        print('wait 5 Second...')
        time.sleep(5)
        print('Disconnect result: {}'.format(mqtt.disconnect()))
    else:
        print('MQTT Connect fail')
