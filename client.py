#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of NSUChat, the Not So Unsafe Chat.
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

from communication import create_socket
import select
import socket
import sys
from time import gmtime, strftime
from communication import synchronize_symm
from crypto import decrypt, encrypt, text2ascii, gen_symm_key
from datetime import datetime

VERSION = 0.1  # Client Application Protocol Version
nickname = ''
serverPort = ''


def prompt(brdcast=True, who='', msg=''):
    if brdcast is True:
        sys.stdout.write(strftime('[%H:%M:%S] ', gmtime()) + '<You> ')
        sys.stdout.flush()
    else:
        if '[Server]' in who:
            sys.stdout.write(strftime('[%H:%M:%S] ', gmtime()) + who
                         + msg)
            sys.stdout.flush()
        else:
            sys.stdout.write(strftime('\n[%H:%M:%S] ', gmtime()) + who
                         + msg)
            sys.stdout.flush()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        try:
            print "Please, answer the following questions."
            while len(nickname) == 0 or nickname[0] == ' ':
                nickname = raw_input("Nickname: ")
            server_ip = raw_input("Server IP/Name: ")
            if server_ip == '':
                print 'Using localhost...'
                server_ip = '0.0.0.0'
            while len(serverPort) == '' or serverPort == '':
                serverPort = raw_input("Server Port: ")
            serverPort = int(serverPort)
        except KeyboardInterrupt:
            print "\nQuitting.."
            sys.exit()
    elif len(sys.argv) != 3:
        print 'Usage: python client.py nickname server:port'
        sys.exit()
    else:
        try:
            nickname = sys.argv[1]
            serverPort = sys.argv[2]
            # If server was informed in the commandline argument
            if len(serverPort.split(':')) == 2:
                serverPort = int(serverPort.split(':')[1])
                server_ip = serverPort.split(':')[0]
            else:
                serverPort = int(serverPort)
                server_ip = '0.0.0.0'
        except ValueError:
            print 'Server port must be an integer.'
            sys.exit()

    if serverPort > 65535:
        print 'Server port must be lower than 65535.'
    else:
        client_socket = create_socket(serverPort, server_ip)
        print 'Connected to the chat server'

    while True:
        try:
            socket_list = [sys.stdin, client_socket]
            # Get the list sockets which are readable
            read_sockets, write_sockets, error_sockets = select.select(
                                                        socket_list, [], [])
        except KeyboardInterrupt:
            print "\nQuitting..."
            sys.exit()
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
                            if len(nickname) <= int(data[2]):
                                # synchronize Data Unit (Client SYN_SYMM)
                                ip = socket.gethostbyname(socket.gethostname())
                                seconds = datetime.now().second
                                ascii = text2ascii(nickname)
                                symm_key = gen_symm_key(ip, seconds, ascii)
                                client_socket.send(
                                    synchronize_symm(nickname, symm_key)
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
                        # Decrypt incoming message
                        data = decrypt(data, symm_key)
                        if data[0] == '#':
                            if data[1] == '#':
                                print 'There is already someone logged in ' +\
                                      'as ' + data[2:]
                                print 'Quitting...'
                                sys.exit()
                            # First time you're gonna send something
                            print "Four-way handshake finished. Welcome " +\
                                  data[1:] + '.'
                            prompt()
                        # Broadcast messages
                        elif data[0] == '$':
                            # Entered/left room messages and public messages
                            sys.stdout.write(data[1:])
                            prompt()
                        # Nicklist reply
                        elif data[0] == '|':
                            if data[1] == '|':
                                prompt(False, data[2:])
                                prompt()
                            else:
                                prompt(False, '[Server] ', 'Users: ' +
                                       data[1:] + '\n')
                                prompt()
                        elif data[0] == '^':
                            for i, char in enumerate(data):
                                if char == ',':
                                    pos = i
                                    break
                            prompt(False, '[Private message from ' + data[1:pos]
                            + '] ' + data[pos + 1:])
                            prompt()
                        else:
                            sys.stdout.write(data[1:])
                            prompt()

            #user entered a message
            else:
                try:
                    msg = sys.stdin.readline()
                    message = encrypt(msg, symm_key)
                    client_socket.send(message)
                    # If a command has just been run, do not show prompt
                    if '/nicklist' in msg:
                        pass
                    else:
                        prompt()
                except (KeyboardInterrupt, IndexError):
                    print '\nQuitting...'
                    sys.exit()
