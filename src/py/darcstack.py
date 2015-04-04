#!/usr/bin/env python
# -*- coding: latin-1 -*-
#

# usage:
# darc_prototype.py <filename>
#
from __future__ import print_function

from bitstring import BitArray
from darccrc import Crc

class DarcStack:
  # Constants
  PRINT_L3 = False
  PRINT_L4 = True
  PRINT_L5 = True
  REPAIR_L2 = True
  CRC_L2 = True
  CRC_L3 = True
  CRC_L4 = True
  CRC_L5 = True

  crc = Crc()

  # BICs from ETSI EN 300 751 Table 2
  BICs = (['0x135e', '0x74a6', '0xa791', '0xc875'])

  def __init__(self):
    # Static Variables
    self.SeCh_data = BitArray(length=8*304) # max 304 bytes, see 8.3.1
    self.LMCh_data = BitArray(length=8*256) # max 256 bytes

    self.lmch_blocknumber = 0

    self.scramble_table = BitArray('0b10101111101010101000000101001010111100101110111000000111001110100100111101011101010001001000011001110000101111011011001101000011101111000011111111100000111101111100010111001100100000100101001110110100011110011111001101100010101001000111000110110101011100010011000100010000') 

    if self.REPAIR_L2:
      # Load offline syndrome table
      self.syndrome_table = []
      try:
        with open("syndrome82") as f: # open the file for reading
          print("Reading syndrome file")
          for line in f: # iterate over each line
            syndrome, datastring = line.split() # split it by whitespace
            self.syndrome_table.append((syndrome, datastring))
      except:
        print("ERROR could not open syndrome file")
      self.syndrome_table = dict(self.syndrome_table)


  # @return:  valid       - chunk is verified by CRC
  #           bic         - bic number of this block
  #           infoblock   - descrambled, verified/corrected data between
  #                           bic and crc/parity
  def layer2(self, pChunk, pDescramble=True ):
      if len(pChunk) == 288:
        # Check if BIC is BIC 1, 2 or 3
        bic = pChunk[:16]
        if bic == self.BICs[0] or bic == self.BICs[1] or bic == self.BICs[2]:
          # Descramble with Scramble Table (witchcraft!)
          # TODO understand how this table is generated
          # ETSI EN 300 751 7.3.2.6
          if True == pDescramble:
            l2_body = pChunk[16:] ^ self.scramble_table
          else:
            l2_body = pChunk[16:]

          l2_infoblock = l2_body[:176]
          l2_crc = l2_body[176:176+14]
          l2_parity = l2_body[176+14:176+14+82]

          decode = False
          if self.REPAIR_L2:
            if self.crc.crc14(BitArray(l2_infoblock)) != l2_crc:
              print('L2 CRC Fail')

              syndrome = self.crc.crc82(BitArray(l2_body[0:176+14]),l2_parity)
              #print(str(syndrome))
              syndrome.prepend('0b00')
              # Search for syndrome in precalculated table
              if str(syndrome) in self.syndrome_table:
                print('found')
                datastring = BitArray(self.syndrome_table[str(syndrome)])
                datastring = datastring[2:] #remove leading 2 bits
                #print(str(syndrome))
                # Apply error vector on data
                l2_infoblock = l2_body[:176] ^ datastring[:176]
                l2_crc = l2_body[176:176+14] ^ datastring[176:176+14]
              else:
                print('syndrome not found')
                decode = False
            else:
              decode = True

          if self.CRC_L2 and not decode:
            if self.crc.crc14(BitArray(l2_infoblock)) == l2_crc:
              decode = True

          if decode:
            self.layer3(bic, l2_infoblock)
            return True
          else:
            return False

        elif bic == self.BICs[3]: # BIC 4
          # Vertical Parity Block
          # TODO Support Frames as described in ETSI EN 300 751 7.3.3.2
          # for now, only BICs 1-3 are supported and handled.
          # No vertical parity is evaluated.
          return True

      return False

  def layer3a(self, pChunk):
      if len(pChunk) == 192:
        bic = pChunk[:16]
        l2_body = pChunk[16:]
        self.layer3(bic, l2_body)


  def layer3(self, pBic, pInfoblock):
    SILCh = pInfoblock[:4]
    SILCh = SILCh[::-1] # Marshalling 

    if SILCh == '0x8':  # Service Channel (SeCh)
      # 8.3.2
      SeCh_LF = pInfoblock[5]
      SeCh_DUP = pInfoblock[6:8]
      SeCh_CID = pInfoblock[8:12]
      SeCh_CID = SeCh_CID[::-1]
      SeCh_TYPE = pInfoblock[12:16]
      SeCh_TYPE = SeCh_TYPE[::-1]
      SeCh_NID = pInfoblock[16:20]
      SeCh_NID = SeCh_NID[::-1]
      SeCh_BLN = pInfoblock[20:24]
      SeCh_BLN = SeCh_BLN[::-1]

      # Marshalling of l3_body
      # TODO beautify and pack into function
      data = BitArray(length=152)
      for pos in range(len(data)):
       if not (pos % 8):
          word = pInfoblock[24+pos:24+pos+8]
          word = word[::-1]
          data[pos:pos+8] = word

      if self.PRINT_L3:
        print('l3\tSeCh\t' + str(data))
        print('\t\tLF\tDUP\tCID\tTYPE\tNID\tBLN')
        print('\t\t' + str(SeCh_LF) + '\t' \
               + str(SeCh_DUP) + '\t' \
               + str(SeCh_CID) + '\t' \
               + str(SeCh_TYPE) + '\t' \
               + str(SeCh_NID) + '\t' \
               + str(SeCh_BLN))
      
      # Store data to SeCh Msg Buffer,
      # dissect and print on Last Fragment
      if '0x0' == SeCh_BLN:
        # copy data of first fragment incl SeCh Header
        self.SeCh_data[:152] = data
      else:
        # we dont need to copy the SeCh Header again
        idx = 24+(SeCh_BLN.uint*128)
        self.SeCh_data[idx:idx+128] = data[24:]
          
      if True == SeCh_LF:
        SeCh_ECC = self.SeCh_data[0:8]
        SeCh_TSEID = self.SeCh_data[8:15]
        SeCh_ML = self.SeCh_data[15:24]

        if self.PRINT_L3:
          print('\t\tECC\tTSEID\tML')
          print('\t\t' + str(SeCh_ECC) + '\t' \
                  + str(SeCh_TSEID.uint) + '\t' \
                  + str(SeCh_ML.uint))
          print('')

        if '0x0' == SeCh_TYPE:
          self.layer3_SeCh_COT(SeCh_ML.uint)
        elif '0x1' == SeCh_TYPE:
          self.layer3_SeCh_AFT()
        elif '0x2' == SeCh_TYPE:
          self.layer3_SeCh_SAFT()
        elif '0x3' == SeCh_TYPE:
          self.layer3_SeCh_TDPNT()
        elif '0x4' == SeCh_TYPE:
          self.layer3_SeCh_SNT()
        elif '0x5' == SeCh_TYPE:
          self.layer3_SeCh_TDT()
        elif '0x6' == SeCh_TYPE:
          self.layer3_SeCh_SCOT(SeCh_ML.uint)
        else:
          print('layer3\terror\tunkown SeCh TYPE')


    elif SILCh == '0x9':    # Short Message (SMCh)
      # 8.4.2
      SMCh_DI = pInfoblock[4]
      SMCh_LF = pInfoblock[5]
      SMCh_SC = pInfoblock[6:10]
      SMCh_SC = SMCh_SC[::-1]
      SMCh_CRC = pInfoblock[10:16]

      if self.PRINT_L3:
        print('l3\tSMCh\tDI\tLF\tSC\tCRC')
        print('\t\t' + str(SMCh_DI) + '\t' \
                + str(SMCh_LF) + '\t' \
                + str(SMCh_SC) + '\t' \
                + str(SMCh_CRC))
        print('Dissection of SMCh not implemented yet')
      # TODO Marshalling of l3_body

    elif SILCh == '0xA':    # Long Message (LMCh)
      # 8.5.2
      LMCh_DI = pInfoblock[4]
      LMCh_LF = pInfoblock[5]
      LMCh_SC = pInfoblock[6:10]
      LMCh_SC = LMCh_SC[::-1]
      LMCh_CRC = pInfoblock[10:16]


      # Marshalling of l3_body
      # TODO beautify and pack into function
      # 2 byte L3 Header, 20 Byte L3 data
      data = BitArray(length=160)
      for pos in range(len(data)):
       if not (pos % 8):
          word = pInfoblock[16+pos:16+pos+8]
          word = word[::-1]
          data[pos:pos+8] = word


      if self.PRINT_L3:
          print('l3\tLMCh\tDI\tLF\tSC\tCRC')
          print('\t\t' + str(LMCh_DI) + '\t' \
                  + str(LMCh_LF) + '\t' \
                  + str(LMCh_SC) + '\t' \
                  + str(LMCh_CRC))
          
          if self.CRC_L3:
            if self.crc.crc6(BitArray(pInfoblock[:10])) == LMCh_CRC:
              print('\tL3 CRC OK')
            else:
              print('\tL3 CRC FALSE')

          print('\t\t' + data)

      idx = self.lmch_blocknumber*160
      self.LMCh_data[idx:idx+160] = data
      self.lmch_blocknumber += 1
      
      if True == LMCh_LF:
        self.lmch_blocknumber = 0
        self.layer4_LMCh()

    elif SILCh == '0xB':    # Block Message (BMCh)
      # 8.6.1
      data = BitArray(length=160)
      BMCh_OFFEXT = 0
      for pos in range(len(data)):
        if not (pos % 8):
          word = pInfoblock[16+pos:16+pos+8]
          word = word[::-1]
          data[pos:pos+8] = word
      BMCh_DI = pInfoblock[4]
      BMCh_SCh = pInfoblock[5:8]
      BMCh_RFA = pInfoblock[8:12]
      BMCh_Mtype = pInfoblock[12:16]
      BMCh_FNO = data[3:8]
      BMCh_DUP = data[1:3]
      BMCh_BLK = data[0]

      BMCh_US = data[8]
      BMCh_LS = data[9:16]

      BMCh_EXT1 = data[16]
      BMCh_SID1 = data[17:24]
      if True == BMCh_EXT1:
        BMCh_EXTSID1 = data[24:31]
        BMCh_RFA1 = data[31]
        BMCh_OFFEXT += 8
      else:
        BMCh_EXTSID1 = 0x0000000
        BMCh_RFA1 = False
      BMCh_CS1 = data[24+BMCh_OFFEXT]
      BMCh_OFF1 = data[25+BMCh_OFFEXT:32+BMCh_OFFEXT]
      BMCh_MSG1 = data[32+BMCh_OFFEXT:40+BMCh_OFFEXT]

      BMCh_EXT2 = data[40+BMCh_OFFEXT]
      BMCh_SID2 = data[41+BMCh_OFFEXT:48+BMCh_OFFEXT]
      if True == BMCh_EXT2:
        BMCh_EXTSID2 = data[48+BMCh_OFFEXT:55+BMCh_OFFEXT]
        BMCh_RFA2 = data[55+BMCh_OFFEXT]
        BMCh_OFFEXT += 8
      else:
        BMCh_EXTSID2 = 0x0000000
        BMCh_RFA2 = False
      BMCh_CS2 = data[48+BMCh_OFFEXT]
      BMCh_OFF2 = data[49+BMCh_OFFEXT:56+BMCh_OFFEXT]
      BMCh_MSG2 = data[56+BMCh_OFFEXT:64+BMCh_OFFEXT]

      BMCh_EXT3 = data[64+BMCh_OFFEXT]
      BMCh_SID3 = data[65+BMCh_OFFEXT:72+BMCh_OFFEXT]
      if True == BMCh_EXT3:
        BMCh_EXTSID3 = data[72+BMCh_OFFEXT:79+BMCh_OFFEXT]
        BMCh_RFA3 = data[79+BMCh_OFFEXT]
        BMCh_OFFEXT += 8
      else:
        BMCh_EXTSID3 = 0x0000000
        BMCh_RFA3 = False
      BMCh_CS3 = data[72+BMCh_OFFEXT]
      BMCh_OFF3 = data[73+BMCh_OFFEXT:80+BMCh_OFFEXT]
      BMCh_MSG3 = data[80+BMCh_OFFEXT:88+BMCh_OFFEXT]

      BMCh_EXT4 = data[88+BMCh_OFFEXT]
      BMCh_SID4 = data[89+BMCh_OFFEXT:96+BMCh_OFFEXT]
      if True == BMCh_EXT4:
        BMCh_EXTSID4 = data[96+BMCh_OFFEXT:103+BMCh_OFFEXT]
        BMCh_RFA4 = data[103+BMCh_OFFEXT]
        BMCh_OFFEXT += 8
      else:
        BMCh_EXTSID4 = 0x0000000
        BMCh_RFA4 = False
      BMCh_CS4 = data[96+BMCh_OFFEXT]
      BMCh_OFF4 = data[97+BMCh_OFFEXT:104+BMCh_OFFEXT]
      BMCh_MSG4 = data[104+BMCh_OFFEXT:112+BMCh_OFFEXT]

      if BMCh_OFFEXT <= 24: #If less then 3 Extended, room for one more

        BMCh_EXT5 = data[88+24+BMCh_OFFEXT]
        BMCh_SID5 = data[89+24+BMCh_OFFEXT:96+24+BMCh_OFFEXT]
        if True == BMCh_EXT5:
          BMCh_EXTSID5 = data[96+24+BMCh_OFFEXT:103+24+BMCh_OFFEXT]
          BMCh_RFA5 = data[103+24+BMCh_OFFEXT]
          BMCh_OFFEXT += 8
        else:
          BMCh_EXTSID5 = 0x0000000
          BMCh_RFA5 = False
        BMCh_CS5 = data[96+24+BMCh_OFFEXT]
        BMCh_OFF5 = data[97+24+BMCh_OFFEXT:104+24+BMCh_OFFEXT]
        BMCh_MSG5 = data[104+24+BMCh_OFFEXT:112+24+BMCh_OFFEXT]     

      if BMCh_OFFEXT == 0: #If less no Extended, room for one more

        BMCh_EXT6 = data[88+48+BMCh_OFFEXT]
        BMCh_SID6 = data[89+48+BMCh_OFFEXT:96+48+BMCh_OFFEXT]
        if True == BMCh_EXT6:
          BMCh_EXTSID6 = data[96+48+BMCh_OFFEXT:103+48+BMCh_OFFEXT]
          BMCh_RFA6 = data[103+48+BMCh_OFFEXT]
          BMCh_OFFEXT += 8
        else:
          BMCh_EXTSID6 = 0x0000000
          BMCh_RFA6 = False
        BMCh_CS6 = data[96+48+BMCh_OFFEXT]
        BMCh_OFF6 = data[97+48+BMCh_OFFEXT:104+48+BMCh_OFFEXT]
        BMCh_MSG6 = data[104+48+BMCh_OFFEXT:112+48+BMCh_OFFEXT] 




      if True:
        print('l3\tBMCh\tDI\tSCh\tMtype\tRFA\tBLK\tDUP\tFNO\tUS\tLS')
        print('\t\t' + str(BMCh_DI)  + '\t' \
                     + str(BMCh_SCh) + '\t' \
                     + str(BMCh_Mtype) + '\t' \
                     + str(BMCh_RFA) + '\t' \
                     + str(BMCh_BLK) + '\t' \
                     + str(BMCh_DUP) + '\t' \
                     + str(BMCh_FNO.uint) + '\t' \

                     + str(BMCh_US) + '\t' \
                     + str(BMCh_LS) + '\t' \

                     )

        print('SID\tEXT\tSID\tEXTSID\tRFA\tCS\tOFF\tMSG')
        print('1:\t'
              + str(BMCh_EXT1) + '\t' \
              + str(BMCh_SID1.uint) + '\t' \
              + str(BMCh_EXTSID1) + '\t' \
              + str(BMCh_RFA1) + '\t' \
              + str(BMCh_CS1) + '\t' \
              + str(BMCh_OFF1.uint) + '\t' \
              + str(BMCh_MSG1.uint)
                     )
        print('2:\t'
              + str(BMCh_EXT2) + '\t' \
              + str(BMCh_SID2.uint) + '\t' \
              + str(BMCh_EXTSID2) + '\t' \
              + str(BMCh_RFA2) + '\t' \
              + str(BMCh_CS2) + '\t' \
              + str(BMCh_OFF2.uint) + '\t' \
              + str(BMCh_MSG2.uint)
                     )
        print('3:\t'
              + str(BMCh_EXT3) + '\t' \
              + str(BMCh_SID3.uint) + '\t' \
              + str(BMCh_EXTSID3) + '\t' \
              + str(BMCh_RFA3) + '\t' \
              + str(BMCh_CS3) + '\t' \
              + str(BMCh_OFF3.uint) + '\t' \
              + str(BMCh_MSG3.uint)
                     )
        print('4:\t'
              + str(BMCh_EXT4) + '\t' \
              + str(BMCh_SID4.uint) + '\t' \
              + str(BMCh_EXTSID4) + '\t' \
              + str(BMCh_RFA4) + '\t' \
              + str(BMCh_CS4) + '\t' \
              + str(BMCh_OFF4.uint) + '\t' \
              + str(BMCh_MSG4.uint)
                     )
        if BMCh_OFFEXT <= 24: #If less then 3 Extended, room for one more
          print('5:\t'
                + str(BMCh_EXT5) + '\t' \
                + str(BMCh_SID5.uint) + '\t' \
                + str(BMCh_EXTSID5) + '\t' \
                + str(BMCh_RFA5) + '\t' \
                + str(BMCh_CS5) + '\t' \
                + str(BMCh_OFF5.uint) + '\t' \
                + str(BMCh_MSG5.uint)
                      )

        if BMCh_OFFEXT == 0: #If less no Extended, room for one more
          print('6:\t'
                + str(BMCh_EXT6) + '\t' \
                + str(BMCh_SID6.uint) + '\t' \
                + str(BMCh_EXTSID6) + '\t' \
                + str(BMCh_RFA6) + '\t' \
                + str(BMCh_CS6) + '\t' \
                + str(BMCh_OFF6.uint) + '\t' \
                + str(BMCh_MSG6.uint)
                     )



        

      # Marshalling of l3_body
      # TODO beautify and pack into function
      # 2 byte L3 Header, 20 Byte L3 data
      #print('Block:' + str(data) +'\n' )


    else:
      # unknown logical channel id
      #print('layer3\terror\tunknown logical channel id')
      return

  def layer3_SeCh_COT(self, pMsgLen):

      if self.PRINT_L3:
        print('\t\tCOT\tSID\tSA\tCA\tSCA')

        msg = ''
        i = 24
        while i < (pMsgLen+3)*8:
          msg += '\t\t\t' \
                  + str(self.SeCh_data[i:i+14].uint) + '\t' \
                  + str(self.SeCh_data[i+15]) + '\t' \
                  + str(self.SeCh_data[i+14])
          if self.SeCh_data[i+14]:
            msg += '\t' + str(self.SeCh_data[i+16:i+24])
            i += 24
          else:
            msg += '\tnone'
            i += 16
          msg += '\n'
        print(msg)
        print('')

  def layer3_SeCh_AFT(self):
    if self.PRINT_L3:
      print('layer3\terror\tSeCh AFT not implemented yet')
      print('')

  def layer3_SeCh_SAFT(self):
    # 8.3.3.3
    if self.PRINT_L3:
      print('layer3\terror\tSeCh SAFT not implemented yet')
      print('')


  def layer3_SeCh_TDPNT(self):
    if self.PRINT_L3:
      print('layer3\terror\tSeCh TDPNT not implemented yet')
      print('')

  def layer3_SeCh_SNT(self):
    if self.PRINT_L3:
      print('layer3\terror\tSeCh SNT not implemented yet')
      print('')

  def layer3_SeCh_TDT(self):
    # 8.3.3.6
    if self.PRINT_L3:
        print('\t\tTDT\tTIME\t' \
                + str(self.SeCh_data[25:30].uint) + ':' \
                + str(self.SeCh_data[30:36].uint) + ':' \
                + str(self.SeCh_data[36:42].uint))
        print('\t\t\tETA\tOffset\tTAF')
        print('\t\t\t' \
                + str(self.SeCh_data[24]) + '\t' \
                + str(self.SeCh_data[42:48].uint) + '\t' \
                + str(self.SeCh_data[48:56].uint))
        print('')

        print('\t\t\tMDT\t' \
                + str(self.SeCh_data[57:74]))

        # Network Name Length
        networkNameLength = self.SeCh_data[74:78].uint

        # Position Flag
        positionFlag = self.SeCh_data[78]

        networkName = ''
        if 0 < networkNameLength < 16:
          i = 0
          while i < networkNameLength:
            networkName += chr(self.SeCh_data[80+(i*8):80+(i*8)+8].uint)
            i += 1
          print('\t\t\tNetwork Name:\t' + networkName)

        if positionFlag:
          print('\t\t\tPosition Flag not implemented yet')

        print('')

  def layer3_SeCh_SCOT(self, pMsgLen):
    if self.PRINT_L3:
        print('\t\tSCOT\tSID\tCY\tDT')

        msg = ''
        i = 24
        while i < (pMsgLen+3)*8:
          msg += '\t\t\t'
          if self.SeCh_data[i]:
            msg += str(self.SeCh_data[i+1:i+15].uint) + '\t' \
                    + str(self.SeCh_data[i+16:i+19].uint) + '\t' \
                    + str(self.SeCh_data[i+19:i+24].uint)
            i += 24
          else:
            msg += str(self.SeCh_data[i+1:i+8].uint) + '\t' \
                    + str(self.SeCh_data[i+8:i+11].uint) + '\t' \
                    + str(self.SeCh_data[i+11:i+16].uint)
            i += 16
          msg += '\n'
        print(msg)
        print('')


  def layer4_LMCh(self):

    LMCh_RI = self.LMCh_data[0:2]
    LMCh_CI = self.LMCh_data[2:4]
    LMCh_FL = self.LMCh_data[4:6]
    LMCh_EXT = self.LMCh_data[6]
    

    if LMCh_EXT:
      LMCh_ADD = self.LMCh_data[7:21]
      LMCh_COM = self.LMCh_data[24]
      LMCh_CAF = self.LMCh_data[25]
      LMCh_UDL = self.LMCh_data[26:34]

      if LMCh_CAF:
        LMCh_LMCCA_IM = self.LMCh_data[34:44]
        LMCh_LMCCA_EXT = self.LMCh_data[44]
        LMCh_LMCCA_RP = self.LMCh_data[45]
        LMCh_LMCCA_PARITY = self.LMCh_data[46]
        LMCh_LMCCA_SCRMODE = self.LMCh_data[47:49]
        LMCh_LMCCA_UPDATEECM = self.LMCh_data[49]
        if LMCh_LMCCA_EXT:
          LMCh_LMCCA_MM = self.LMCh_data[50:52]
          LMCh_LMCCA_ECMId = self.LMCh_data[52:58]
          LMCh_CRC = self.LMCh_data[58:64]
          LMCh_data_start = 64
        else:
          LMCh_CRC = self.LMCh_data[50:56]
          LMCh_data_start = 56
      else:
        LMCh_CRC = self.LMCh_data[34:40]
        LMCh_data_start = 40

    else:
      LMCh_ADD = self.LMCh_data[7:16]
      LMCh_COM = self.LMCh_data[16]
      LMCh_CAF = self.LMCh_data[17]
      LMCh_UDL = self.LMCh_data[18:26]

      if LMCh_CAF:
        LMCh_LMCCA_IM = self.LMCh_data[26:36]
        LMCh_LMCCA_EXT = self.LMCh_data[36]
        LMCh_LMCCA_RP = self.LMCh_data[37]
        LMCh_LMCCA_PARITY = self.LMCh_data[38]
        LMCh_LMCCA_SCRMODE = self.LMCh_data[39:41]
        LMCh_LMCCA_UPDATEECM = self.LMCh_data[41]
        if LMCh_LMCCA_EXT:
          LMCh_LMCCA_MM = self.LMCh_data[42:44]
          LMCh_LMCCA_ECMId = self.LMCh_data[44:50]
          LMCh_CRC = self.LMCh_data[50:56]
          LMCh_data_start = 56
        else:
          LMCh_CRC = self.LMCh_data[42:48]
          LMCh_data_start = 48
      else:
        LMCh_CRC = self.LMCh_data[26:32]
        LMCh_data_start = 32


    if self.PRINT_L4:
      print('l4\tLMCh\tRI\tCI\tFL\tEXT?\tADD\tCOM\tCAF?\tUDL')
      print('\t\t' + str(LMCh_RI) + '\t' \
              + str(LMCh_CI) + '\t' \
              + str(LMCh_FL) + '\t' \
              + str(LMCh_EXT) + '\t' \
              + str(LMCh_ADD.uint) + '\t' \
              + str(LMCh_COM) + '\t' \
              + str(LMCh_CAF) + '\t' \
              + str(LMCh_UDL.uint))
      print('')

    if self.CRC_L4:  
      if self.crc.crc6(BitArray(self.LMCh_data[0:LMCh_data_start-6])) == LMCh_CRC:
          self.layer5(LMCh_data_start, LMCh_UDL.uint*8, LMCh_ADD.uint)
    else:
      self.layer5(LMCh_data_start, LMCh_UDL.uint*8, LMCh_ADD.uint)
    
  def layer5(self, pDataStart, pDataLength, pAddress):
    if self.PRINT_L5:
      idx = pDataStart
      L5_TYPE = self.LMCh_data[idx:idx+4]

      if '0x4' == L5_TYPE: # L5 Packet Type
        L5_CRCFLAG = self.LMCh_data[idx+4]
        L5_COMPRFLAG = self.LMCh_data[idx+5]
        L5_FRAGFLAG = self.LMCh_data[idx+6]


        #print('l5\t\tTYPE\tCRC?\tCOMPR?\tFRAG?')
        #print('\t\t' \
                #+ str(L5_TYPE) + '\t' \
                #+ str(L5_CRCFLAG) + '\t' \
                #+ str(L5_COMPRFLAG) + '\t' \
                #+ str(L5_FRAGFLAG))

        if L5_CRCFLAG:
          L5_CRC = self.LMCh_data[idx+pDataLength-16:idx+pDataLength]
          pDataLength = pDataLength-16

        if not L5_FRAGFLAG:
          work = False
          if True == L5_CRCFLAG:
            if True == self.CRC_L5:
              # CRC Flag set in Msg and disabled in our stack, so check it
              if self.crc.crc16(BitArray(self.LMCh_data[pDataStart+8:pDataStart+pDataLength])) == L5_CRC:
                work = True
              else:
                print('L5 CRC Fail')
            else:
              # CRC Flag set in Msg, but disabled in our stack, so
              # we accept everything
              work = True
          else:
            # CRC Flag disabled in Msg, accept everything
            work = True

          if True == work:
            #print(str(self.LMCh_data[idx+8:idx+pDataLength]))
            #print('')

            i = 0
            msg = '  '
            while i < pDataLength:
              idx = i + pDataStart + 8
              char = self.LMCh_data[idx:idx+8].uint
              if (char >= 48 and char <=57) \
                or (char >= 65 and char <= 90) \
                or (char >= 97 and char <= 122) \
                or (char >= 0xC0 and char <= 0xFF):
                msg += ' ' + chr(char)
              else:
                msg += ' .'
              i += 8
            #print(msg)

            # Write output to file 
            if self.LMCh_data[pDataStart+8:pDataStart+32] == '0x000001':
              fh = open('layer5_output','a')
              msg = str(pAddress) + ' ' \
                      + str(self.LMCh_data[pDataStart+8:pDataStart+pDataLength]) + '\n' \
                      + str(pAddress) + ' ' \
                      + msg + '\n'
              fh.write(msg)
              fh.close()

            # Print Output
            if True:
              #fh = open('layer5_output','a')
              msg = str(pAddress) + ' ' \
                      + str(self.LMCh_data[pDataStart+8:pDataStart+pDataLength]) + '\n' \
                      + str(pAddress) + ' ' \
                      + msg + '\n'
              print(msg)
              #fh.close()
        else:
          print('l5\terror\tfragmented packets not implemented yet')

      else:
        print('l5\terror\ttype not implemented yet')

      print('===========================================================')
