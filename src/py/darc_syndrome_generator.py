#!/usr/bin/env python

# this script will win the prize for the slowest
# script ever.
from __future__ import print_function
from bitstring import BitArray
from sys import argv

from darccrc import Crc

def gen_syndrome(pBits):
  errorfield = ([BitArray('0b1'), \
                  BitArray('0b11')])

  # build all possible error combinations as 
  # block errors
  for length in range(3,pBits+1):
    # set first and last bit of errorstring and
    # count up in between
    for i in range(2**(length-2)):
      error = BitArray('0b1')
      error.append(BitArray(uint=i, length=length-2))
      error.append('0b1')
      errorfield.append(error)

  for i in errorfield:
    
    error = i
    length = len(error)

    print(error)
    fh = open('syndrome82','a+')
    # place block errors in every possible position in
    # data string
    for pos in range(190-length+1):
      datastring = BitArray(length=190-length-pos)
      datastring.append(error)
      datastring.append(BitArray(length=pos))
      # generate syndrome from datastring
      syndrome = crc.crc82(datastring)

      # make strings a multiple of 4 bit for nicer printing
      datastring.prepend('0b00')
      syndrome.prepend('0b00')

      fh.write(str(syndrome) + ' ' + str(datastring) + '\n')

    fh.close()


if __name__ == '__main__':

  crc = Crc()

  amount_of_bits = int(argv[1])
  gen_syndrome(amount_of_bits)



