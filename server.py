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

from communication import listen_for_conn
import sys

max_conn_request = 32    # Max number of connection requests concurrently
max_nick_size = 6        # Max nickname length allowed
max_msg_length = 100     # Max length of text message
version = "0.1"          # version
serverPort = None        # Define the port to listen

if __name__ == "__main__":
    if(len(sys.argv) != 2):
        print 'Usage: python server.py port'
        sys.exit()
    else:
        try:
            serverPort = int(sys.argv[1])
        except ValueError:
            print 'Server port must be an integer.'
            sys.exit()
    if serverPort > 65535:
        print 'Server port must be lower than 65535.'
    else:
        # Listening for connections
        listen_for_conn(serverPort, max_conn_request, max_nick_size,
                        max_msg_length, version)
