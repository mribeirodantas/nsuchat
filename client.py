#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (©) 2014 Marcel Ribeiro Dantas
#
# mribeirodantas at fedoraproject.org
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from communication import create_socket
import select
import sys
from time import gmtime, strftime


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
        prompt()

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
                    sys.stdout.write(data)
                    prompt()

            #user entered a message
            else:
                msg = sys.stdin.readline()
                client_socket.send(msg)
                prompt()