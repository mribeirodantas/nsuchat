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

maxBuffer = 1024      # Maximum allowed buffer
CONNECTION_LIST = []  # List to keep track of socket descriptors


# Returns a socket descriptor binding [optional] host to serverPort
# Default host is localhost visible to everybody.
def create_socket(serverPort, host='0.0.0.0', server=False):
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
        # Try to bind socket s to the port serverPort
        try:
            print 'Binding port to hostname..'
            s.bind((host, serverPort))
        except socket.error, msg:
            print 'Failed to bind socket. Error code: ' + str(msg[0]) +\
                  ' Error' + ' message: ' + msg[1]
            sys.exit()
    # If it's a client, connect it to the server socket.
    else:
        # Try to connect to socket s in the specified port serverPort
        try:
            s.connect((host, serverPort))
        except socket.error, msg:
            print 'Failed to connect to socket. Error code: ' + str(msg[0]) +\
                  ' Error message: ' + msg[1]
            sys.exit()

    return s


def listen_for_conn(serverPort, max_conn_request, max_nick_size,
                    max_msg_length, version):

    server_socket = create_socket(serverPort, server=True)

    # Listen to connection requests
    server_socket.listen(max_conn_request)
    print 'Chat server started on port ' + str(serverPort)
    print 'Maximum number of connected users: ' + str(max_conn_request)

    # Add server socket to the list of readable connections
    CONNECTION_LIST.append(server_socket)

    while True:
        # Get the list sockets which are ready to be read through select
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
                # Handle the case in which there is a new connection received
                # through server_socket
                sockfd, addr = server_socket.accept()
                CONNECTION_LIST.append(sockfd)
                print 'Client (%s, %s) connected' % addr

                broadcast_data(sockfd, '\n' + strftime('[%H:%M:%S] ',
                               gmtime()) + '[%s:%s] entered room\n' % addr,
                               server_socket)

            # Some incoming message from a client
            else:
                # Data received from client, process it
                try:
                    #In Windows, sometimes when a TCP program closes abruptly,
                    # a 'Connection reset by peer' exception will be thrown
                    data = sock.recv(maxBuffer)
                    if data:
                        broadcast_data(sock, '\r' +
                        strftime('[%H:%M:%S] ', gmtime()) + '<' +
                        str(sock.getpeername()) + '> ' + data, server_socket)
                except:
                    broadcast_data(sock, 'Client (%s, %s) is offline' % addr,
                                   server_socket)
                    print 'Client (%s, %s) is offline' % addr
                    sock.close()
                    CONNECTION_LIST.remove(sock)
                    continue

    server_socket.close()


#Function to broadcast chat messages to all connected clients
def broadcast_data(sock, message, server_socket):
    #Do not send the message to master sock    et and the client who has
    #send us the message
    for socket in CONNECTION_LIST:
        if socket != server_socket and socket != sock:
            try:
                socket.send(message)
            except:
                # broken socket connection may be, chat client pressed ctrl+c
                #for example
                socket.close()
                CONNECTION_LIST.remove(socket)
