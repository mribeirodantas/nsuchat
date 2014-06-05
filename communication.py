#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This file is part of NSUChat, the Not So Unsafe Chat.
# This module contains the functions related to establishing connections.
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

import socket
import select
import sys
from time import gmtime, strftime
from crypto import sha1, encrypt, decrypt
import fcntl    # for get_mac
import struct   # for get_mac

MAX_BUFFER = 1024      # Maximum allowed buffer
CONNECTION_LIST = []   # List to keep track of socket descriptors
USERS_LIST = []        # List of connected users


def create_socket(SERVER_PORT, host='0.0.0.0', server=False):
    """Returns a socket descriptor
    The default host for hosting/connecting is localhost visible to everybody.
    If the server flag is True, it will bind the host to the specified port.
    If the server flag is False (default), it will connect to the specified
    host:port"""
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
        if host == '0.0.0.0':
            print 'Setting host as localhost...'
            host = socket.gethostname()
        else:
            print 'Resolving hostname...'
            host = socket.gethostbyname(host)
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
    """Takes a few arguments to start listening for connections to the chat
    serer."""

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

                print '\nClient (%s, %s) connected' % addr

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
                        if register(addr[0], str(sock.fileno()), nickname,
                                symmetric_key, crc) is True:
                            # Encrypt ACK_SYMM message and send it
                            acknowledge(sock, nickname, symmetric_key)
                            print '%s (%s) entered room.' %\
                                  (nickname, addr[0])
                            broadcast(sockfd, '\n' + strftime('[%H:%M:%S] ',
                                   gmtime()) + '[%s] entered room\n' % nickname,
                                   server_socket)
                        else:
                            msg = encrypt('##' + nickname, symmetric_key)
                            server_notice(sock, msg)
                    elif data:
                        for user in USERS_LIST:
                            if str(sock.fileno()) == user[1]:
                                nickname = user[2]
                                symm_key = user[3]
                                message = decrypt(data, symm_key)
                        if message[0] == '/':
                            # Requests list of connected users
                            if message[:9] == '/nicklist':
                                nicklist = request_nicklist()
                                encrypted_nicklist = encrypt(nicklist, symm_key)
                                server_notice(sock, encrypted_nicklist)
                            # Private message
                            elif message[:4] == '/msg':
                                from_nickname = nickname
                                to_nickname = message[5:].split(' ')[0]

                                # What is the target socket?
                                for user in USERS_LIST:
                                    if user[2] == to_nickname:
                                        # Fond target socket ID
                                        dest_socket_id = user[1]
                                        s_k = user[3]
                                for socket in CONNECTION_LIST:
                                    if str(socket.fileno()) == dest_socket_id:
                                        # Found socket descriptor
                                        dest_socket = socket
                                msg = message[5 + len(to_nickname):]
                                data = '^' + from_nickname + ',' + msg
                                encrypted_data = encrypt(data, s_k)
                                server_notice(dest_socket, encrypted_data)
                            # Switch nickname
                            elif message[:6] == '/nick ':
                                new_nick = message[5:].split(' ')[1][0:-1]
                                for user in USERS_LIST:
                                    # Looking for user in USERS_LIST
                                    if (user[1] == str(sock.fileno()) and
                                        user[2] == nickname):
                                            # Register with new nickname
                                            # and check if there is someone
                                            # already with this nickname
                                            if register(user[0],
                                                  str(sock.fileno()), new_nick,
                                                  symmetric_key, crc) is True:
                                                print '%s known as %s.' %\
                                                  (nickname, new_nick)
                                                # Remove o anterior
                                                # Isto porque tupla é imutável
                                                for index, user in \
                                                enumerate(USERS_LIST):
                                                    if user[2] == nickname:
                                                        del USERS_LIST[index]
                                                broadcast(sock, '\n' +
                                                strftime('[%H:%M:%S] ',
                                                gmtime()) + nickname +
                                                'now known as' + new_nick +
                                                '\n', server_socket)
                                            else:
                                                pass
                                                # Falta tratar quando tem gente
                                                # com este nick
                                                #msg = encrypt('##' + nickname, symmetric_key)
                                                #server_notice(sock, msg)
                                broadcast(sock, '\n' +
                                strftime('[%H:%M:%S] ', gmtime()) + '[' +
                                nickname + '] ' + 'is now known as ' +
                                new_nick + '.\n', server_socket)

                                print nickname + ' (%s, %s) is removed' % addr
                            else:
                                reply_error = '||Command not recognized.\n'
                                encrypted_reply = encrypt(reply_error, symm_key)
                                server_notice(sock, encrypted_reply)
                        else:
                            broadcast(sock, '\r' +
                            strftime('[%H:%M:%S] ', gmtime()) + '<' +
                           nickname + '> ' + message, server_socket)
                except:
                    for user in USERS_LIST:
                            if str(sock.fileno()) == user[1]:
                                nickname = user[2]
                    broadcast(sock, '\n' +
                        strftime('[%H:%M:%S] ', gmtime()) + '[' +
                        nickname + '] ' + 'left the room.\n', server_socket)
                    print nickname + ' (%s, %s) is offline' % addr
                    remove_user(str(sock.fileno()))
                    sock.close()
                    CONNECTION_LIST.remove(sock)
                    continue

    server_socket.close()


def wassup(client_socket, MAX_CONN_REQUEST, MAX_NICK_SIZE, MAX_MSG_LENGTH,
           VERSION):
    """First Application Protocol Data Unit of the Four-Way Handshake.
     --------------------------------------------------------------------
    | TYPE | MAX_CONN_REQUEST | MAX_NICK_SIZE | MAX_MSG_LENGTH | VERSION |
    |  *   |                  |               |                |         |
    |______|__________________|_______________|________________|_________|
    |                     ASSYMMETRIC PUBLIC KEY                         |
    |____________________________________________________________________|"""
    wassup = '*,' + str(MAX_CONN_REQUEST) + ',' + str(MAX_NICK_SIZE) + ',' +\
    str(MAX_MSG_LENGTH) + ',' + VERSION
    server_notice(client_socket, wassup)


# *** Falta utilizar chave assimétrica enviada no wassup
# para criptografar esse pacote. E a partir deste, teremos tudo
# criptografado com a simétrica
def synchronize_symm(nickname, s_k):
    """Application Data Protocol sent by client to synchronize its Symmetric Key
    with the server.
     ----------------------------
    | TYPE | NICKNAME | SYMM_KEY |
    |  !   |          |          |
    |______|__________|__________|
    |           SHA-1            |
    |____________________________|"""
    apdu = '!' + nickname + ',' + s_k
    apdu_w_hash = apdu + sha1(apdu)

    return apdu_w_hash


def acknowledge(client_socket, nickname, symm_key):
    """First message encrypted with symm_key
         -------------------------
        | TYPE | NICKNAME | SHA-1 |
        |  #   |          |       |
        |______|__________|_______|"""
    apdu = '#' + nickname
    encrypted_apdu = encrypt(apdu, symm_key)

    server_notice(client_socket, encrypted_apdu)


#     --------------
#    | TYPE | SHA-1 |
#    |  3   |       |
#    |______|_______|
def request_nicklist():
    """Request string list of users registered.
         --------------
        | TYPE | SHA-1 |
        |  |   |       |
        |______|_______|"""
    nicklist = ['|']
    for user in USERS_LIST:
        nicklist.append(user[2])
    # Converts list of strings to a single string
    nicklist = (', ').join(nicklist)
    nicklist = nicklist[0] + nicklist[3:]
    return nicklist


def broadcast(sock, message, server_socket):
    """Function to broadcast chat messages to all connected clients
         --------------
        | TYPE |  MSG  |
        |  $   |       |
        |______|_______|"""
    # Do not send the message to server socket and the client who has
    # sent the message
    for socket in CONNECTION_LIST:
        if socket != server_socket and socket != sock:
            try:
                for user in USERS_LIST:
                    # The user for each specific socket
                    if user[1] == str(socket.fileno()):
                        symm_key = user[3]
                        message = '$' + message
                        msg_encrypted = encrypt(message, symm_key)
                        socket.send(msg_encrypted)
            except:
                # broken socket connection may be, chat client pressed ctrl+c
                # for example
                socket.close()
                CONNECTION_LIST.remove(socket)
                remove_user(str(socket.fileno()))


def server_notice(target_socket, message):
    """Takes a target socket and a message and sends a message to the specified
    socket. This function is supposed to be only used for server notificatoins
    to specific users. For all users, check broadcast.__doc__"""
    # Send the message only to the target
    for socket in CONNECTION_LIST:
        if socket == target_socket:
            try:
                socket.send(message)
            except:
                # broken socket connection may be, chat client pressed ctrl+c
                # for example
                socket.close()
                CONNECTION_LIST.remove(target_socket)
                remove_user(str(target_socket.fileno()))


def register(ip, socket_id, nickname, symm_key, crc):
    """Registers a new identified user in the chat server, along with his
    symmetric key for future encryption/decryption."""
    # Check CRC (missing)
    found = False
    for user in USERS_LIST:
        if user[2] == nickname:
            found = True
    if not found:
        USERS_LIST.append((ip, socket_id, nickname, symm_key))
        for user in USERS_LIST:
            if user[2] == nickname:
                print 'Registering ' + user[2] + '...'
                print 'IP: ' + user[0]
                print 'Symmetric Key: ' + user[3]
                print 'Socket: ' + user[1]
                print 'SHA-1: ' + crc

                return True
    else:
        return False


def remove_user(socket):
    for index, user in enumerate(USERS_LIST):
        if user[1] == socket:
            del USERS_LIST[index]


def get_mac(ifname):
    """Takes an interface name ifname and returns a string containing its
    MAC address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
    return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1]
#print getHwAddr('em1')
