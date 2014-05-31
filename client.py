#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Zapzap client
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

from communication import create_socket
import select
import socket
import sys
from time import gmtime, strftime
from communication import synchronize_symm
from crypto import decrypt, text2ascii, gen_symm_key
from datetime import datetime

VERSION = 0.1  # Client Application Protocol Version


def prompt():
    sys.stdout.write(strftime('[%H:%M:%S] ', gmtime()) + '<You> ')
    sys.stdout.flush()

if __name__ == "__main__":
    if(len(sys.argv) != 3):
        print 'Usage: python client.py nickname port'
        sys.exit()
    else:
        try:
            serverPort = int(sys.argv[2])
        except ValueError:
            print 'Server port must be an integer.'
            sys.exit()
    if serverPort > 65535:
        print 'Server port must be lower than 65535.'
    else:
        client_socket = create_socket(serverPort)
        print 'Connected to the chat server'

    while True:
        socket_list = [sys.stdin, client_socket]
        # Get the list sockets which are readable
        read_sockets, write_sockets, error_sockets = select.select(
                                                        socket_list, [], [])

        for sock in read_sockets:
            #incoming message from remote server
            if sock == client_socket:
                data = sock.recv(4096)
                if not data:
                    print '\nDisconnected from chat server'
                    sys.exit()
                else:
                    # wassup Data Unit (Server ACK)
                    if data[0] == '*':
                        data = data.split(',')
                        print '\nChat server configuration:'
                        print 'Maximum number of connected users: ' +\
                               data[1]
                        print 'Maximum nickname length: ' + data[2]
                        print 'Maximum message length: ' + data[3]
                        print 'Protocol version: ' + data[4] + '\n'
                        if data[4] == str(VERSION):
                            if len(sys.argv[1]) <= int(data[2]):
                                # synchronize Data Unit (Client SYN_SYMM)
                                ip = socket.gethostbyname(socket.gethostname())
                                seconds = datetime.now().second
                                ascii = text2ascii(sys.argv[1])
                                symm_key = gen_symm_key(ip, seconds, ascii)
                                client_socket.send(
                                    synchronize_symm(sys.argv[1], symm_key)
                                    )
                            else:
                                print 'Sorry, your nickname is too long.\n'
                                sys.exit()
                        else:
                            print 'Sorry, version mismatch ocurred.\n' +\
                            'Server Application Protocol Version: ' + data[4] +\
                            '\nClient Application Protocol Version: ' +\
                                                                 str(VERSION)
                            sys.exit()
                    # First Symmetrically encrypted Data Unit
                    # Welcome Data Unit (Server ACK_SYMM)
                    else:
                        # Decrypt ACK_SYMM
                        data = decrypt(data, symm_key)
                        if data[0] == '#':
                            # First time you're gonna send something
                            print "Four-way handshake finished. Welcome " +\
                                  data[1:] + '.'
                            prompt()
                        else:
                            sys.stdout.write(data)
                            prompt()

            #user entered a message
            else:
                msg = sys.stdin.readline()
                client_socket.send(msg)
                prompt()