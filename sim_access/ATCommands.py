#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# ATCommands.py
# @Author :  (Zack Huang)
# @Link   :
# @Date   : 11/26/2021, 4:11:14 PM

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
