#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Communication functions for zapzap.
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

import socket
import select
import sys
from time import gmtime, strftime
from crypto import sha1, encrypt

MAX_BUFFER = 1024      # Maximum allowed buffer
CONNECTION_LIST = []  # List to keep track of socket descriptors


# Returns a socket descriptor
# The default host for hosting/connecting is localhost visible to everybody.
# If the server flag is True, it will bind the host to the specified port.
# If the server flag is False (default), it will connect to the specified
# host:port
def create_socket(SERVER_PORT, host='0.0.0.0', server=False):
    # Try to create a TCP socket object named s
    try:
        print 'Creating socket..'
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print 'Failed to create socket. Error code: ' + str(msg[0]) +\
              ' Error' + ' message: ' + msg[1]
        sys.exit()
    # Try to get local hostname
    try:
        if host != '0.0.0.0':
            print 'Resolving hostname..'
            # gethostname() woud make it locally visible
            host = socket.gethostname()
        else:
            print 'Setting host as localhost..'
    except socket.gaierror:
        #could not resolve
        print 'Hostname could not be resolved. Exiting'
        sys.exit()
    # If it's a server, bind the port to a host.
    if server is True:
        # The line below avoids 'port already in use' warning
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Try to bind socket s to the port SERVER_PORT
        try:
            print 'Binding port to hostname..'
            s.bind((host, SERVER_PORT))
        except socket.error, msg:
            print 'Failed to bind socket. Error code: ' + str(msg[0]) +\
                  ' Error' + ' message: ' + msg[1]
            sys.exit()
    # If it's a client, connect it to the server socket.
    else:
        # Try to connect to socket s in the specified port SERVER_PORT
        try:
            s.connect((host, SERVER_PORT))
        except socket.error, msg:
            print 'Failed to connect to socket. Error code: ' + str(msg[0]) +\
                  ' Error message: ' + msg[1]
            sys.exit()

    return s


# Listens for incoming connections
def listen_for_conn(SERVER_PORT, MAX_CONN_REQUEST, MAX_NICK_SIZE,
                    MAX_MSG_LENGTH, VERSION):

    server_socket = create_socket(SERVER_PORT, server=True)

    # Listen to connection requests
    server_socket.listen(MAX_CONN_REQUEST)
    print 'Chat server started on port ' + str(SERVER_PORT)
    print 'Maximum number of connected users: ' + str(MAX_CONN_REQUEST)

    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)

    while True:
        # Get the list of sockets which are ready to be read through select
        try:
            read_sockets, write_sockets, error_sockets = select.select(
                                                CONNECTION_LIST, [], [])
        except KeyboardInterrupt:
            print '\nClosing socket..'
            server_socket.close()
            print 'Socket closed.'
            sys.exit(1)

        for sock in read_sockets:
            #New connection
            if sock == server_socket:
                # Server socket is about to accept a new connection
                sockfd, addr = server_socket.accept()
                # Register the client socket descriptor in the CONNECTION_LIST
                CONNECTION_LIST.append(sockfd)
                # Application Protocol Three-way Handshake (SYN)
                # Send server information
                wassup(sockfd, MAX_CONN_REQUEST, MAX_NICK_SIZE, MAX_MSG_LENGTH,
           VERSION)

                print 'Client (%s, %s) connected' % addr

            # Some incoming message from a client
            else:
                # Data received from client, process it
                try:
                    #In Windows, sometimes when a TCP program closes abruptly,
                    # a 'Connection reset by peer' exception will be thrown
                    data = sock.recv(MAX_BUFFER)
                    # Application Protocol Three-way Handshake (ACK)
                    if data[0] == "!":
                        nickname = data.split(',')[0][1:]
                        symmetric_key = data.split(',')[1][:-40]
                        crc = data.split(',')[1][-40:]
                        # Register symm_key from this user
                        register(addr[0], sock, nickname, symmetric_key, crc)
                        ## Encrypt ACK_SYMM message and send it
                        acknowledge(sock, nickname, symmetric_key)
                        print '%s (%s) entrou no bate-papo.' %\
                              (nickname, addr[0])
                        broadcast(sockfd, '\n' + strftime('[%H:%M:%S] ',
                               gmtime()) + '[%s] entered room\n' % nickname,
                               server_socket)
                    elif data:
                        broadcast(sock, '\r' +
                        strftime('[%H:%M:%S] ', gmtime()) + '<' +
                       str(sock.getpeername()) + '> ' + data, server_socket)
                except:
                    broadcast(sock, '\nClient (%s, %s) is offline' % addr,
                                   server_socket)
                    print 'Client (%s, %s) is offline' % addr
                    sock.close()
                    CONNECTION_LIST.remove(sock)
                    continue

    server_socket.close()


#     --------------------------------------------------------------------
#    | TYPE | MAX_CONN_REQUEST | MAX_NICK_SIZE | MAX_MSG_LENGTH | VERSION |
#    |  *   |                  |               |                |         |
#    |______|__________________|_______________|________________|_________|
#    |                     ASSYMMETRIC PUBLIC KEY                         |
#    |____________________________________________________________________|
def wassup(client_socket, MAX_CONN_REQUEST, MAX_NICK_SIZE, MAX_MSG_LENGTH,
           VERSION):
    wassup = '*,' + str(MAX_CONN_REQUEST) + ',' + str(MAX_NICK_SIZE) + ',' +\
    str(MAX_MSG_LENGTH) + ',' + VERSION
    server_message(client_socket, wassup)


# *** Falta utilizar chave assimétrica enviada no wassup
# para criptografar esse pacote. E a partir deste, teremos tudo
# criptografado com a simétrica
#     ----------------------------
#    | TYPE | NICKNAME | SYMM_KEY |
#    |  !   |          |          |
#    |______|__________|__________|
#    |           SHA-1            |
#    |____________________________|
def synchronize_symm(nickname, s_k):
    apdu = '!' + nickname + ',' + s_k
    apdu_w_hash = apdu + sha1(apdu)

    return apdu_w_hash


# First message encrypted with symm_key
#     -------------------------
#    | TYPE | NICKNAME | SHA-1 |
#    |  #   |          |       |
#    |______|__________|_______|
def acknowledge(client_socket, nickname, symm_key):
    apdu = '#' + nickname
    encrypted_apdu = encrypt(apdu, symm_key)

    server_message(client_socket, encrypted_apdu)


#     --------------
#    | TYPE | SHA-1 |
#    |  3   |       |
#    |______|_______|
def request_nicklist():
    pass


#     --------------
#    | TYPE |  MSG  |
#    |  $   |       |
#    |______|_______|
# Function to broadcast chat messages to all connected clients
# There is no reason to encrypt such
def broadcast(sock, message, server_socket):
    #Do not send the message to server socket and the client who has
    #sent the message
    for socket in CONNECTION_LIST:
        if socket != server_socket and socket != sock:
            try:
                message = '$' + message
                socket.send(message)
            except:
                # broken socket connection may be, chat client pressed ctrl+c
                #for example
                socket.close()
                CONNECTION_LIST.remove(socket)


def server_message(target_socket, message):
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


def register(ip, socket_descriptor, nickname, symm_key, crc):
    print '\nRegistrar ' + nickname
    print 'IP: ' + ip
    print 'Symmetric Key: ' + symm_key
    print 'SHA-1: ' + crc
