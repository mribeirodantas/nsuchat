#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of NSUChat, the Not So Unsafe Chat.
# This module contains the functions in charge of encrypting the APDUs or that
# are somehow related to those.
#
# Copyright (©) 2014 Marcel Ribeiro Dantas
#
# <mribeirodantas at fedoraproject.org>
#
# NSUChat is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# NSUChat is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with NSUChat. If not, see <http://www.gnu.org/licenses/>.

import hashlib


def sha1(apdu):
    """Takes an Application Protocol Data Unit and returns the respective SHA-1
    hash as an hexadecimal value. It protects the server from obeying to APDUs
    that intentionally arrived modified from what the sender originally sent.
    Integrity is not handled here, since TCP already solves that."""
    sha1 = hashlib.sha1(apdu)

    return sha1.hexdigest()


def text2ascii(text):
    """Takes a text string and returns a string with the list of integer values
    for each character according to ASCII table."""
    ascii = ''
    for char in text:
        ascii = ascii + str(ord(char))

    return ascii


def gen_symm_key(ip, seconds, nickname):
    """Generates a symmetric key that is supposed to be unique to every user in
    the chat server. The symm_key is the concatenation of the IP (joined without
     the dots), the seconds at which the connection was requested and the
     nickname converted into integers according to ASCII table. For more info,
     check text2ascii.__doc__"""
    ip_no_dots = ip.replace('.', '')
    ascii = text2ascii(nickname)
    symm_key = ip_no_dots + str(seconds) + ascii

    return symm_key


def strxor(apdu_with_hash, symm_key):
    """Takes an Application Protocol Data Unit and a symmetric key and xors both
    even when they have different lengths."""
    while len(apdu_with_hash) > len(symm_key):
        symm_key = symm_key + symm_key[:len(apdu_with_hash) - len(symm_key)]
    return "".join([chr(ord(x) ^ ord(y)) for (x, y)
           in zip(apdu_with_hash, symm_key)])


def encrypt(apdu, symm_key):
    """Takes an Application Data Protocol Data Unit and a Symmetric Key.
    Concatenates the apdu with its SHA-1 hash for integrity and requests
    encryption for the strxor function."""
    #Concatenating text with SHA-1 hash of the text
    apdu_with_hash = apdu + sha1(apdu)
    return strxor(apdu_with_hash, symm_key)


def decrypt(encrypted_apdu, symm_key):
    """Takes an encrypted Application Protocol Data Unit and a Symmetric Key and
    decrypts the apdu according to the symm_key informed."""
    decrypted = strxor(encrypted_apdu, symm_key)
    return decrypted[:-40]
