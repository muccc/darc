#!/usr/bin/env python

from bitstring import BitArray

# Generic implementation of Crc
# plus darc-specific crc methods with
# polynoms as stated in ETSI EN 300 751 Chapter 10
class Crc:
  def __init__(self):
    pass

  # @input1 BitArray of Input Message
  # @input2 BitArray of CRC Polynom
  # @input3 BitArray of CRC Start Value
  # @return BitArray of CRC Result Value
  def crc(self, pMsg, pPolynom, pCode):

      crclen = len(pPolynom)-1
      #print(pPolynom)
      msg = pMsg + pCode
      for i in range(len(msg)-crclen):
          if msg[i] == True:
              for j in range(len(pPolynom)):
                  msg[i+j] = msg[i+j] ^ pPolynom[j]
      #print msg[-crclen:]
      return msg[-crclen:]

  # L3 Short Message, Long Message
  # L4 Long Message
  def crc6(self, pMsg, pCode=BitArray(length=6)):
      # x^6 + x^4 + x^3 + 1
      return self.crc(pMsg, \
                  BitArray('0b1011001'), \
                  pCode)

  # L4 Short Message
  def crc8(self, pMsg, pCode=BitArray(length=8)):
      # x^8 + x^5 + x^4 + x^3 + 1
      return self.crc(pMsg, \
                  BitArray('0b100111001'), \
                  pCode)

  # L2
  def crc14(self, pMsg, pCode=BitArray(length=14)):
      # x^14 + x^11 + x^2 +1
      return self.crc(pMsg, \
                  BitArray('0b100100000000101'), \
                  pCode)

  # L5 data group
  # some specialties with data inversion as defined in standard
  def crc16(self, pMsg, pCode=BitArray(length=16)):
      # invert first 16 bit of input data
      pMsg[:16] = ~pMsg[:16]
      # x^16 + x^12 + x^5 +1
      # invert CRC before output
      return ~(self.crc(pMsg, \
                    BitArray('0b10001000000100001'), \
                    pCode))

  # L2 parity
  def crc82(self, pMsg, pCode=BitArray(length=82)):
      # 11.1
      return self.crc(pMsg, \
                  BitArray('0b10000110000100011000000000100010001000000010001010000000001010001000000010000010001'), \
                  pCode)
