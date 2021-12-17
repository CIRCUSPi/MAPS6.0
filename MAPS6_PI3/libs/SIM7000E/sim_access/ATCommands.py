#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ATCommands.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 4:11:14 PM

import binascii


def ucs2encode(text):
    if text is None or text == '':
        return ''
    return text.encode('utf-16-be').hex().upper()


def ucs2decode(text):
    if text is None or text == '':
        return ''
    return binascii.unhexlify(text).decode('utf-16-be')


def atcmd(cmd, extended):
    assert isinstance(cmd, str)
    if extended:
        cmd = 'AT+{0}'.format(cmd.upper())
    else:
        cmd = 'AT{0}'.format(cmd.upper())
    return cmd


def atread(cmd, extended):
    assert isinstance(cmd, str)
    if extended:
        cmd = 'AT+{0}?'.format(cmd.upper())
    else:
        cmd = 'AT{0}?'.format(cmd.upper())
    return cmd


def atset(cmd, extended):
    assert isinstance(cmd, str)
    if extended:
        cmd = 'AT+{0}='.format(cmd.upper())
    else:
        cmd = 'AT{0}='.format(cmd.upper())
    return cmd


class ATCommands(object):

    @classmethod
    def test(cls):
        return 'AT\r\n'

    @classmethod
    def module_setecho(cls, enable):
        if enable == False:
            return atcmd('E', False) + '0\r\n'
        else:
            return atcmd('E', False) + '1\r\n'

    @classmethod
    def module_checkready(cls):
        return atread('CPIN', True) + '\r\n'

    @classmethod
    def network_setapn(cls, apn):
        return atset('CSTT', True) + '\"{0}\"\r\n'.format(apn)

    @classmethod
    def network_attach(cls):
        return atset('CGATT', True) + '1\r\n'

    @classmethod
    def network_bringup(cls):
        return atcmd('CIICR', True) + '\r\n'

    @classmethod
    def network_ipaddr(cls):
        return atcmd('CIFSR', True) + '\r\n'

    @classmethod
    def get_apn(cls):
        return atcmd('CGNAPN', True) + '\r\n'

    @classmethod
    def read_network_attach(cls):
        return atread('CGATT', True) + '\r\n'

    @classmethod
    def shut_PDP(cls):
        return atcmd('CIPSHUT', True) + '\r\n'

    @classmethod
    def tcp_connect(cls, ip, port):
        return atset('CIPSTART', True) + '\"TCP\",\"{}\",{}\r\n'.format(str(ip), str(port))

    @classmethod
    def tcp_status(cls):
        return atcmd('CIPSTATUS', True) + '\r\n'

    @classmethod
    def csq(cls):
        return atcmd('CSQ', True) + '\r\n'

    @classmethod
    def tcp_send(cls, dataLen):
        return atset('CIPSEND', True) + '{}\r\n'.format(str(dataLen))

    @classmethod
    def tcp_close(cls):
        return atcmd('CIPCLOSE', True) + '\r\n'

    @classmethod
    def tcp_send_ack(cls):
        return atcmd('CIPACK', True) + '\r\n'

    @classmethod
    def tcp_setRxGet_Manual(cls):
        return atset('CIPRXGET', True) + '1\r\n'

    @classmethod
    def tcp_chkData(cls):
        return atset('CIPRXGET', True) + '4\r\n'

    @classmethod
    def tcp_readData(cls, len):
        ''' output data can not exceed 1460 bytes at a time.
        '''
        return atset('CIPRXGET', True) + '2,{}\r\n'.format(len)

    @classmethod
    def tcp_readHEXData(cls, len):
        ''' output data can not exceed 730 bytes at a time.
        '''
        return atset('CIPRXGET', True) + '3,{}\r\n'.format(len)

    @classmethod
    def tcp_setTxHex(cls):
        return atset('CIPSENDHEX', True) + '1\r\n'
    
    @classmethod
    def Gnss_Pwr_on(cls):
        return atset('CGNSPWR', True) + '1\r\n'
    
    @classmethod
    def Gnss_Navigation_info(cls):
        return atcmd('CGNSINF', True) + '\r\n'


if __name__ == '__main__':
    import inspect
    attrs = (getattr(ATCommands, name) for name in dir(ATCommands))
    methods = filter(inspect.ismethod, attrs)
    for method in methods:
        try:
            print(method())
        except TypeError:
            # Can't handle methods with required arguments.
            pass
