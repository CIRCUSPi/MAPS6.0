#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# mega2560.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 12/15/2021, 11:46:29 AM

import logging
import time

logger = logging.getLogger(__name__)

MAPS_LEADING_CMD = 0xAA
MAPS_GET_SENSOR_ALL_CMD = 0xB5
MAPS_SET_POLLING_SENSOR_CMD = 0xC6


class Mega2560(object):
    def __init__(self, serial):
        self.__port = serial
        self.__sensor_data = {
            'TEMP': 0,  # (℃)
            'HUMI': 0,  # (%RH)
            'CO2': 0,  # (ppm)
            'AVE_CO2': 0,  # (ppm)
            'TVOC': 0,  # (ppb)
            'eCO2': 0,  # (ppm)
            'S_H2': 0,  # (Raw)
            'S_ETHANOL': 0,  # (Raw)
            'BASELINE_TVOC': 0,  # (Raw)
            'BASELINE_eCO2': 0,  # (Raw)
            'Illuminance': 0,  # (Lux)
            'Color_Temperature': 0,  # (°K)
            'CH_R': 0,  # (Raw)
            'CH_G': 0,  # (Raw)
            'CH_B': 0,  # (Raw)
            'CH_C': 0,  # (Raw)
            'PM1.0_AE': 0,  # (ug/m3)
            'PM2.5_AE': 0,  # (ug/m4)
            'PM10.0_AE': 0,  # (ug/m5)
            'PM1.0_SP': 0,  # (ug/m3)
            'PM2.5_SP': 0,  # (ug/m4)
            'PM10.0_SP': 0,  # (ug/m5)
        }

    def __Not(self, byte):
        return ~byte & 0xFF

    def __Calc_checkSum(self, datas):
        return (sum([(data) ^ ((idx + 1) % 0x100) for idx, data in enumerate(datas)]) & 0xFF)

    def __2byte_to_int16(self, _2byte):
        return ((_2byte[1] << 8) | _2byte[0])

    def __wait_echo_command(self, echo_cmd, timeout=1000):
        timeout = time.time() + (timeout / 1000)
        while(time.time() < timeout):
            while(self.__port.inWaiting() >= 2):
                bytes_data = self.__port.read(2)
                if(bytes_data[0] == MAPS_LEADING_CMD and bytes_data[1] == echo_cmd):
                    return True
        self.__port.read_all()
        logger.error(f'echo_cmd: {echo_cmd:02X} error.')
        return False

    def get_sensor_all(self):
        data = bytearray()
        data.append(MAPS_LEADING_CMD)
        data.append(self.__Not(MAPS_LEADING_CMD))
        data.append(MAPS_GET_SENSOR_ALL_CMD)
        data.append(self.__Not(MAPS_GET_SENSOR_ALL_CMD))

        self.__port.write(bytes(data))
        if(not self.__wait_echo_command(MAPS_GET_SENSOR_ALL_CMD)):
            return self.__sensor_data

        # read all data
        data = bytearray(self.__port.read(44))
        # calc checksum
        data.insert(0, MAPS_GET_SENSOR_ALL_CMD)
        data.insert(0, MAPS_LEADING_CMD)
        rcv_checksums = self.__port.read(2)
        checksum = self.__Calc_checkSum(data)
        if (rcv_checksums[0] != checksum or rcv_checksums[1] != self.__Not(checksum)):
            self.__port.read_all()
            logger.error('read sensor all data error.')
            return self.__sensor_data
        # read sensor data
        self.__sensor_data['TEMP'] = (self.__2byte_to_int16(data[2:4])/100)
        self.__sensor_data['HUMI'] = (self.__2byte_to_int16(data[4:6])/100)
        self.__sensor_data['CO2'] = self.__2byte_to_int16(data[6:8])
        self.__sensor_data['AVE_CO2'] = self.__2byte_to_int16(data[8:10])
        self.__sensor_data['TVOC'] = self.__2byte_to_int16(data[10:12])
        self.__sensor_data['eCO2'] = self.__2byte_to_int16(data[12:14])
        self.__sensor_data['S_H2'] = self.__2byte_to_int16(data[14:16])
        self.__sensor_data['S_ETHANOL'] = self.__2byte_to_int16(data[16:18])
        self.__sensor_data['BASELINE_TVOC'] = self.__2byte_to_int16(
            data[18:20])
        self.__sensor_data['BASELINE_eCO2'] = self.__2byte_to_int16(
            data[20:22])
        self.__sensor_data['Illuminance'] = self.__2byte_to_int16(data[22:24])
        self.__sensor_data['Color_Temperature'] = self.__2byte_to_int16(
            data[24:26])
        self.__sensor_data['CH_R'] = self.__2byte_to_int16(data[26:28])
        self.__sensor_data['CH_G'] = self.__2byte_to_int16(data[28:30])
        self.__sensor_data['CH_B'] = self.__2byte_to_int16(data[30:32])
        self.__sensor_data['CH_C'] = self.__2byte_to_int16(data[32:34])
        self.__sensor_data['PM1.0_AE'] = self.__2byte_to_int16(data[34:36])
        self.__sensor_data['PM2.5_AE'] = self.__2byte_to_int16(data[36:38])
        self.__sensor_data['PM10.0_AE'] = self.__2byte_to_int16(data[38:40])
        self.__sensor_data['PM1.0_SP'] = self.__2byte_to_int16(data[40:42])
        self.__sensor_data['PM2.5_SP'] = self.__2byte_to_int16(data[42:44])
        self.__sensor_data['PM10.0_SP'] = self.__2byte_to_int16(data[44:46])
        return self.__sensor_data

    def set_sensor_all_polling(self):
        return self.set_sensor_polling(True, True, True, True, True, True)

    def set_sensor_polling(self, temp, co2, tvoc, light, pms, rtc):
        data = bytearray()
        data.append(MAPS_LEADING_CMD)
        data.append(self.__Not(MAPS_LEADING_CMD))
        data.append(MAPS_SET_POLLING_SENSOR_CMD)
        data.append(self.__Not(MAPS_SET_POLLING_SENSOR_CMD))
        data.append(temp)
        data.append(co2)
        data.append(tvoc)
        data.append(light)
        data.append(pms)
        data.append(rtc)
        checksum = self.__Calc_checkSum(data)
        data.append(checksum)
        data.append(self.__Not(checksum))

        self.__port.write(bytes(data))
        if(not self.__wait_echo_command(MAPS_SET_POLLING_SENSOR_CMD)):
            return False
        bytes_data = self.__port.read(2)
        return (bytes_data[0] == 0x00 and bytes_data[1] == 0xFF)
