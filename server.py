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

from communication import listen_for_conn
import sys

MAX_CONN_REQUEST = 32    # Max number of connection requests concurrently
MAX_NICK_SIZE = 6        # Max nickname length allowed
MAX_MSG_LENGTH = 100     # Max length of text message
VERSION = "0.1"          # version
SERVER_PORT = 2020        # Define the port to listen

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print 'Usage: python server.py port'
        sys.exit()
    else:
        try:
            SERVER_PORT = int(sys.argv[1])
        except ValueError:
            print 'Server port must be an integer.'
            sys.exit()
    if SERVER_PORT > 65535:
        print 'Server port must be lower than 65535.'
    else:
        # Listening for connections
        listen_for_conn(SERVER_PORT, MAX_CONN_REQUEST, MAX_NICK_SIZE,
                        MAX_MSG_LENGTH, VERSION)
