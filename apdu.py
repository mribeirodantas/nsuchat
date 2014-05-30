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

# What's up Application Protocol Data Unit
# Everybody is welcomed to the server with this Data Unit containing basic
# information to allow proper connection.

from communication import CONNECTION_LIST

#     --------------------------------------------------------------------
#    | TYPE | MAX_CONN_REQUEST | MAX_NICK_SIZE | MAX_MSG_LENGTH | VERSION |
#    |  *   |                  |               |                |         |
#    |______|__________________|_______________|________________|_________|
#    |                     ASSYMMETRIC PUBLIC KEY                         |
#    |____________________________________________________________________|
def wassup(client_socket, MAX_CONN_REQUEST, MAX_NICK_SIZE, MAX_MSG_LENGTH,
           VERSION):
    wassup = '*' + str(MAX_CONN_REQUEST) + ',' + str(MAX_NICK_SIZE) + ',' +\
    str(MAX_MSG_LENGTH) + ',' + VERSION
    private_message(client_socket, wassup)


#Function to broadcast chat messages to all connected clients
def broadcast(sock, message, server_socket):
    #Do not send the message to server socket and the client who has
    #sent the message
    for socket in CONNECTION_LIST:
        if socket != server_socket and socket != sock:
            try:
                socket.send(message)
            except:
                # broken socket connection may be, chat client pressed ctrl+c
                #for example
                socket.close()
                CONNECTION_LIST.remove(socket)


def private_message(target_socket, message):
    #Send the message only to the target
    for socket in CONNECTION_LIST:
        if socket == target_socket:
            try:
                socket.send(message)
            except:
                # broken socket connection may be, chat client pressed ctrl+c
                #for example
                socket.close()
                CONNECTION_LIST.remove(target_socket)
