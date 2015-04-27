# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import binascii

from Crypto.Cipher import Blowfish


class Crypto(object):

    def __init__(self, key, padding_char='='):
        self._cipher = Blowfish.new(key, Blowfish.MODE_ECB)
        self.padding_char = padding_char

    def _pad(self, text):
        if text.endswith(self.padding_char):
            raise ValueError("text should not finish with %s characters" %
                             self.padding_char)
        return text + (8 - len(text) % 8) * self.padding_char

    def _unpad(self, text):
        return text.rstrip(self.padding_char)

    def encrypt(self, clear_text):
        """Encrypt a string"""
        encrypted = self._cipher.encrypt(self._pad(clear_text))
        return binascii.b2a_hex(encrypted)

    def decrypt(self, encrypted_text):
        """Decrypt a string"""
        try:
            encrypted = binascii.a2b_hex(encrypted_text)
            return self._unpad(self._cipher.decrypt(encrypted))
        except (TypeError, ValueError):
            return ""


def encrypt(text, key):
    return Crypto(key).encrypt(text)


def decrypt(text, key):
    return Crypto(key).decrypt(text)
