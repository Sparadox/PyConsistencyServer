#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Testing backend for consistency, just run the program it will send an update message to
consistency and exit
"""

import socket

consistency_socket = socket.socket()
consistency_socket.connect(("localhost", 4321))
consistency_socket.send('{"message": "update", "data":{"uri": "uri1"}}'.encode('utf-8'))
consistency_socket.close()

