#!/usr/bin/env python
# -*- coding: latin-1 -*-
#

# usage:
# darc_prototype.py <filename>
#

from sys import argv
from bitstring import Bits

from darcstack import DarcStack
import socket


if __name__ == '__main__':
    #UDP_IP = "192.168.1.152"
    UDP_IP = "127.0.0.1"
    UDP_PORT = 51337
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    darcstack = DarcStack()

    while True:
        data, addr = sock.recvfrom(24)
        #darcstack.layer2(Bits(bytes=data),False)
        darcstack.layer3a(Bits(bytes=data))
