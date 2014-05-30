#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This module contains the functions in charge of encrypting the APDUs or that
# are somehow related to those.
#
# Copyright (©) 2014 Marcel Ribeiro Dantas
#
# <mribeirodantas at fedoraproject.org>
#
# This file is part of zapzap.
#
# Zapzap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Zapzap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with zapzap. If not, see <http://www.gnu.org/licenses/>.

import hashlib


# Takes an Application Protocol Data Unit and returns the SHA-1 hash
# as an hexadecimal value. It protects the server from obeying to apdus
# that intentionally arrived modified from what the sender sent. Integrity
# is not handled here, since TCP already solves that.
def sha1(apdu):
    sha1 = hashlib.sha1(apdu)

    return sha1.hexdigest()


def text2ascii(text):
    ascii = ''
    for char in text:
        ascii = ascii + str(ord(char))

    return ascii


# The symm_key is the concatenation of the IP (joined without the dots), the
# seconds at which the connection was requested and the nickname converted into
# ASCII (integer for each char).
def symm_key(ip, seconds, nickname):
    ip_no_dots = ip.replace('.', '')
    ascii = text2ascii(nickname)
    symm_key = ip_no_dots + str(seconds) + ascii

    return symm_key


def strxor(apdu, symm_key):     # xor two strings of different lengths
    while len(apdu) > len(symm_key):
        symm_key = symm_key + symm_key[:len(apdu) - len(symm_key)]
    return "".join([chr(ord(x) ^ ord(y)) for (x, y)
           in zip(apdu, symm_key)])


# Takes APDU + SYMM_KEY
# Outputs APDU cryptoed with SYMM_KEY
def crypto(apdu, symm_key):
    #Concatenating text with SHA-1 hash of the text
    apdu_with_hash = apdu + sha1(apdu)
    return strxor(apdu_with_hash, symm_key)