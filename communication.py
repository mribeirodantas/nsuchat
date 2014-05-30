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

# Server function that will listen for connections from chat clients

import socket
import select
import sys
from time import gmtime, strftime
from datetime import datetime
from crypto import text2ascii, sha1, symm_key

MAX_BUFFER = 1024      # Maximum allowed buffer
CONNECTION_LIST = []  # List to keep track of socket descriptors


# Returns a socket descriptor
# The default host for hosting/connecting is localhost visible to everybody.
# If the server flag is True, it will bind the host to the specified port.
# If the server flag is False, it will connect to the specified host:port
# it will bind the socket t
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

                broadcast(sockfd, '\n' + strftime('[%H:%M:%S] ',
                               gmtime()) + '[%s:%s] entered room\n' % addr,
                               server_socket)

            # Some incoming message from a client
            else:
                # Data received from client, process it
                try:
                    #In Windows, sometimes when a TCP program closes abruptly,
                    # a 'Connection reset by peer' exception will be thrown
                    data = sock.recv(MAX_BUFFER)
                    # Application Protocol Three-way Handshake (ACK)
                    if data[0] == "!":
                        print '%s (%s) entrou no bate-papo.' %\
                        (data.split(',')[0][1:], addr[0])
                    elif data:
                        broadcast(sock, '\r' +
                        strftime('[%H:%M:%S] ', gmtime()) + '<' +
                       str(sock.getpeername()) + '> ' + data, server_socket)
                except:
                    broadcast(sock, 'Client (%s, %s) is offline' % addr,
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
    private_message(client_socket, wassup)


# *** Falta utilizar chave assimétrica enviada no wassup
# para criptografar esse pacote. E a partir deste, teremos tudo
# criptografado com a simétrica
#     -------------------------
#    | TYPE | NICKNAME | SHA-1 |
#    |  !   |          |       |
#    |______|__________|_______|
#    |     SYMMETRIC KEY       |
#    |_________________________|
def acknowledge(nickname):
    ip = socket.gethostbyname(socket.gethostname())
    seconds = datetime.now().second
    ascii = text2ascii(nickname)
    s_k = symm_key(ip, seconds, ascii)

    apdu = '!' + nickname + ',' + s_k
    apdu_w_hash = apdu + sha1(apdu)

    return apdu_w_hash


#     --------------
#    | TYPE | SHA-1 |
#    |  3   |       |
#    |______|_______|
def request_nicklist():
    pass


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
