#!/usr/bin/env python
# -*- coding: latin-1 -*-
#

# usage:
# darc_prototype.py <filename>
#

from sys import argv
from bitstring import Bits
from bitstring import BitArray

from darcstack import DarcStack

if __name__ == '__main__':

    darcstack = DarcStack()

    filename = argv[1]
    f = Bits(filename=filename)
    
    x = 0
    while x < len(f):
        valid = darcstack.layer2(f[x:x+288])

        if valid:
            # if CRC/Parity check is successful, 
            # make a jump of x+288 to increase processing speed
            x += 288
        else:
            x += 1        

