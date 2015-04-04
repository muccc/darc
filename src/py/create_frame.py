#!/usr/bin/env python
# -*- coding: latin-1 -*-
#

# usage:
# darc_prototype.py <filename>
#

from sys import argv
from bitstring import Bits

#from darcstack import DarcStack
from bitstring import BitArray
from bitarray import bitarray
from array import array
from darccrc import Crc
from darcstack import DarcStack
import binascii

L3_SUP = 0
L3_SC = 0
FrameCnt = 0
darcstack = DarcStack()
L2Frame = []

def layer2(Message):
    global L3_SC
    global L2Frame
    
    scramble_table = BitArray('0b10101111101010101000000101001010111100101110111000000111001110100100111101011101010001001000011001110000101111011011001101000011101111000011111111100000111101111100010111001100100000100101001110110100011110011111001101100010101001000111000110110101011100010011000100010000') 
    crc = Crc()
    if L3_SC == 0:
        L2Frame = []
        print("Create Frame: " + str(FrameCnt) + "...this will take a while")
    #print(L3_SC)
    if L3_SC < 190:
        if L3_SC < 60: #BIC 1
            L2_BIC = BitArray('0xA791', length = 16)
        else:
            if L3_SC >= 60 and L3_SC < 130:
                L2_BIC = BitArray('0x74A6', length = 16)
            else:
                L2_BIC = BitArray('0x135E', length = 16)
        L2_CRC = crc.crc14(Message)
        L2_MSGCRC = Message + L2_CRC
        L2_Parity = crc.crc82(L2_MSGCRC)
        L2Block = L2_BIC + Message + L2_CRC + L2_Parity
        #print(L3_SC)
        L2Frame.insert(L3_SC,L2Block)
        #print(str(L2Block))
        #print(str(L2Frame[L3_SC]))
        if L3_SC == 189:
            k = 0
            while k < 82:
                L2Frame.append(BitArray('0xc875', length = 16))
                L2Frame[190+k].append(BitArray(length = 272))
                k+=1
                
            i = 0
            j = 0
            while i < 272:
                VerticalBlock = BitArray(length=190)
                while j < 190:
                    Block = L2Frame[j]
                    VerticalBlock.set(Block[i+16],j)
                    j+=1
                j = 0
                VerticalCRC = crc.crc82(VerticalBlock)
                k = 0
                while k < 82:
                    L2Frame[190+k].set(VerticalCRC[k],i+16)
                    k+=1
                i+=1
            l = 0
####SCRAMBLE HERE
            i = 0
            while i < 272:
                Scramble = L2Frame[i][16:288] ^ scramble_table
                L2Frame[i] = L2Frame[i][0:16]+Scramble
                i+=1

#################



            fh = open('frame_output','a')
            msg = ''
            while l < len(L2Frame):
                #print(str(L2Frame[l]))
                m = 0
                while m < len(L2Frame[l]):
                    if (m%8 == 0):
                         msg += chr(L2Frame[l][m:m+8].uint)
                    m+=1
                l+=1
            fh.write(msg)                   
            fh.close()
                
        ####Test
        #L2Block[117] = False ## Parity Test
        #darcstack.layer2(L2Block) 

def layer3(Message, type, ServiceType = BitArray('0x0110',length=4)):
    global L3_SC
    global L3_SUP

    crc = Crc()
    if '0xA' == type: ## Long Message
        #print(str(Message))
        L3_Fragment = (len(Message)/160)+1
        data = BitArray(length = L3_Fragment*160)
        data.set(0)
        for pos in range(len(Message)):
            data[pos] = Message[pos] #fill data
        #print(str(data))
        #print(str(L3_Fragment) + ' ' + str(len(data)))
        i = 0
        while i < L3_Fragment:
            L3Hdr_LCh = BitArray('0b1010', length = 4) # Long Message
            L3Hdr_DI= BitArray('0b0', length = 1) # No Decode Indicator
            if i < L3_Fragment -1:
                L3Hdr_LF = BitArray('0b0', length = 1) # Not the End
            else:
                L3Hdr_LF = BitArray('0b1', length = 1) # the End
            L3Hdr_SC = BitArray(uint = L3_SC%16, length=4) # Counter
            L3Hdr_LCh = L3Hdr_LCh[::-1] #Flip LSB/MSB
            L3Hdr_SC = L3Hdr_SC[::-1] #Flip LSB/MSB
            L3Hdr_PreCRC = L3Hdr_LCh + L3Hdr_DI + L3Hdr_LF + L3Hdr_SC 
            L3Hdr_CRC = crc.crc6(L3Hdr_PreCRC)
            L3Hdr = L3Hdr_LCh + L3Hdr_DI + L3Hdr_LF + L3Hdr_SC +L3Hdr_CRC
            dataFragment = data[0+(160*i):160+(160*i)]
            # Marshalling of l3_body
            # TODO beautify and pack into function
            # 2 byte L3 Header, 20 Byte L3 data
            #data_ = BitArray(length=160)
            for pos in range(len(dataFragment)):
                if not (pos % 8):
                    word = dataFragment[pos:pos+8]
                    word = word[::-1]
                    dataFragment[pos:pos+8] = word
            #print(str(dataFragment))
            L3Packet = L3Hdr + dataFragment
            i+=1
            #print(str(L3Packet))
            layer2(L3Packet)
            L3_SC+=1

    if '0xB' == type: ## Block Message
        L3Hdr_LCh = BitArray('0b1011', length = 4) # Bloc Message
        L3Hdr_DI= BitArray('0b0', length = 1) # No Decode Indicator
        L3Hdr_SCh = BitArray('0b100', length = 3) # Not the End
        L3Hdr_LCh = L3Hdr_LCh[::-1] #Flip LSB/MSB
        L3Hdr_SCh = L3Hdr_SCh[::-1] #Flip LSB/MSB
        L3Hdr = L3Hdr_LCh + L3Hdr_DI + L3Hdr_SCh
        data = BitArray(length = 168)
        data.set(0)
        for pos in range(len(Message)):
            data[pos] = Message[pos] #fill data
        dataFragment = data[0:168]
        # Marshalling of l3_body
        # TODO beautify and pack into function
        # 2 byte L3 Header, 20 Byte L3 data
        #data_ = BitArray(length=160)
        for pos in range(len(dataFragment)):
            if not (pos % 8):
                word = dataFragment[pos:pos+8]
                word = word[::-1]
                dataFragment[pos:pos+8] = word
        L3Packet = L3Hdr + dataFragment
        #print(str(L3Packet))
        layer2(L3Packet)
        L3_SC+=1

    if '0x8' == type: ## Service Message
        
        L3_Fragment = (len(Message)/152)+1
        data = BitArray(length = L3_Fragment*152)
        data.set(0)
        for pos in range(len(Message)):
            data[pos] = Message[pos] #fill data
        #print(str(data))
        #print(str(L3_Fragment) + ' ' + str(len(data)))
        i = 0
        while i < L3_Fragment:
            L3Hdr_LCh = BitArray('0b1000', length = 4) # Service Message
            L3Hdr_LCh = L3Hdr_LCh[::-1]
            L3Hdr_RFA= BitArray('0b0', length = 1) # No Future
            if i < L3_Fragment -1:
                L3Hdr_LF = BitArray('0b0', length = 1) # Not the End
            else:
                L3Hdr_LF = BitArray('0b1', length = 1) # the End
            L3Hdr_DUP = BitArray(uint = L3_SUP%4, length=2) # Counter
            L3Hdr_CID = BitArray('0xD', length=4) # Germany
            L3Hdr_CID = L3Hdr_CID[::-1]
            L3Hdr_Type = ServiceType
            L3Hdr_Type = L3Hdr_Type[::-1]
            L3Hdr_NID = BitArray('0xC', length=4) #MVG
            L3Hdr_NID = L3Hdr_NID[::-1]
            L3Hdr_BLN = BitArray(uint=(L3_Fragment-1)%16, length=4) #Blocknumber
            L3Hdr_BLN = L3Hdr_BLN[::-1]

            L3Hdr = L3Hdr_LCh + L3Hdr_RFA + L3Hdr_LF + L3Hdr_DUP + L3Hdr_CID + L3Hdr_Type + L3Hdr_NID + L3Hdr_BLN

            dataFragment = data[0+(152*i):152+(152*i)]
            # Marshalling of l3_body
            # TODO beautify and pack into function
            # 2 byte L3 Header, 20 Byte L3 data
            #data_ = BitArray(length=160)
            for pos in range(len(dataFragment)):
                if not (pos % 8):
                    word = dataFragment[pos:pos+8]
                    word = word[::-1]
                    dataFragment[pos:pos+8] = word
            #print(str(dataFragment))
            L3Packet = L3Hdr + dataFragment
            i+=1
            #print(str(L3Packet))
            layer2(L3Packet)
            L3_SC+=1



def layer4_LMch(LMCh, SubChanID):
    crc = Crc()
    #L5HDR
    L5Hdr_type = BitArray('0b0100', length = 4) # L5 Packet
    L5Hdr_CRCFlag = BitArray('0b1', length = 1) # Use CRC
    L5Hdr_COMPRFlag = BitArray('0b0', length = 1) # No Compression
    L5Hdr_FRAGFlag = BitArray('0b0', length = 1) # No Fragmentation
    L5Hdr_RFAFlag = BitArray('0b0', length = 1) # No Future



    L5Hdr = L5Hdr_type + L5Hdr_CRCFlag + L5Hdr_COMPRFlag + L5Hdr_FRAGFlag + L5Hdr_RFAFlag
    L5Body = L5Hdr + LMCh
    L5CRC = crc.crc16(L5Body[8:len(L5Body)])   #Maybe without Header?????
    L5Packet = L5Hdr + LMCh + L5CRC
    
    #print(str(L5Packet))
    #print(str(len(L5Packet)))

        #L4Hdr
    L4Hdr_RI = BitArray('0b00', length = 2) # No Index
    L4Hdr_CI = BitArray('0b00', length = 2) # No Continuity
    L4Hdr_FL = BitArray('0b11', length = 2) # The one and only
    L4Hdr_EXT = BitArray('0b0', length = 1) # No Extended ID
    L4Hdr_ADD = BitArray(uint = SubChanID, length=9) # 9 Bit Subchannel ID
    L4Hdr_COM = BitArray('0b0', length = 1) # Data Message
    L4Hdr_CAF = BitArray('0b0', length = 1) # No CA
    L4Hdr_Length = BitArray(uint=(len(L5Packet)/8),length=8) # DataLength
    L4HdrToCRC = L4Hdr_RI + L4Hdr_CI + L4Hdr_FL + L4Hdr_EXT + L4Hdr_ADD + L4Hdr_COM + L4Hdr_CAF + L4Hdr_Length
    L4Hdr_CRC = crc.crc6(L4HdrToCRC)
    L4Hdr = L4Hdr_RI + L4Hdr_CI + L4Hdr_FL + L4Hdr_EXT + L4Hdr_ADD + L4Hdr_COM + L4Hdr_CAF + L4Hdr_Length + L4Hdr_CRC
    L4Packet = L4Hdr + L5Packet
    #print(str(L4Packet))
    layer3(L4Packet,'0xA')

   # L5test = BitArray('0x4021414243',length=40)
    #L5testCRC=crc.crc16(L5test)
    #L5testpring = L5test + L5testCRC
    #print(str(L5testpring))

def blockMessage(Framecnt, MsgNo, SChanID):
    BMSG_MType = BitArray('0b0000', length = 4) # Frame Message
    BMSG_MType = BitArray('0b0000', length = 4) # Not used
    BMSG_Blk = BitArray('0b0', length = 1) # Start at 0
    BMSG_DUP = BitArray(uint=Framecnt%4,length=2) # We update every time :) 
    BMSG_FNO = BitArray(uint=Framecnt%24,length=5) #Frame No
    BMSG_US = BitArray('0b0', length = 1) # Everything is Specified
    BMSG_LS = BitArray('0b1111111', length = 7) # Not finished yet :)
    ### We just send ONE Channel
    BMSG_EXT = BitArray('0b0', length = 1) # No extensions
    BMSG_SID = BitArray(uint=SChanID,length=7) # Channel ID 
    BMSG_CS = BitArray('0b0', length = 1) # Message only in one Frame
    BMSG_OFF = BitArray(uint=0, length = 7) # No Offset for only one Message
    BMSG_MSG = BitArray(uint=MsgNo%256, length = 8) # Number of Messages

    BMSG = BMSG_MType + BMSG_MType + BMSG_Blk + BMSG_DUP + BMSG_FNO + BMSG_US + BMSG_LS + BMSG_EXT + BMSG_SID + BMSG_CS + BMSG_OFF + BMSG_MSG

    layer3(BMSG,'0xB')

def fillFrame(SChanID):
    global L3_SUP

    SrvMSG_ECC = BitArray('0xe0', length = 8) # Extended Country Code
    SrvMSG_TSEID = BitArray('0b0000001',length = 7)
    #SCOT ###################
    SrvMSG_ML = BitArray(uint=2, length = 9) # Length
    SrvMSG_EXT = BitArray('0b0', length = 1) # No Extended ID
    SrvMSG_SID = BitArray(uint=SChanID,length=7) # Channel ID 
    SrvMSG_CY = BitArray('0b000', length = 3) # We send every Frame!!!
    SrvMSG_DT = BitArray('0b00000', length = 5) # We send every Frame!!!
    SrvMSG = SrvMSG_ECC + SrvMSG_TSEID + SrvMSG_ML + SrvMSG_EXT + SrvMSG_SID + SrvMSG_CY + SrvMSG_DT
    layer3(SrvMSG,'0x8',BitArray('0b0110', length = 4))
    #########################
    #TDT ####################
    SrvMSG_ML = BitArray(uint=2, length = 9) # Length
    SrvMSG_ETA = BitArray('0b0', length = 1) # We Have no good Time :)
    SrvMSG_Hours = BitArray(uint=23,length=5) # 23:42:05
    SrvMSG_Min = BitArray(uint=42,length=6) # 23:42:05
    SrvMSG_Sec = BitArray(uint=15,length=6) # 23:42:05
    SrvMSG_LTO = BitArray('0b000000',length=6) # We have UTC
    SrvMSG_TAF = BitArray('0b00000001',length=8) # We have UTC
    SrvMSG_TIME = SrvMSG_ETA + SrvMSG_Hours + SrvMSG_Min + SrvMSG_Sec + SrvMSG_LTO + SrvMSG_TAF

    SrvMSG_RFA = BitArray('0b0', length = 1) # No Future
    SrvMSG_MJD = BitArray('0b01101111010101011',length = 17) #Date
    SrvMSG_NNL = BitArray('0x3', length = 4) # NetworkNameLength
    SrvMSG_PF = BitArray('0b0', length = 1) # No Position
    SrvMSG_DATE = SrvMSG_RFA + SrvMSG_MJD + SrvMSG_NNL + SrvMSG_PF + SrvMSG_RFA

    SrvMSG_NNF = BitArray('0x6D7667') #mvg
    SrvMSG = SrvMSG_ECC + SrvMSG_TSEID + SrvMSG_ML + SrvMSG_TIME + SrvMSG_DATE + SrvMSG_NNF
    layer3(SrvMSG,'0x8',BitArray('0b0101', length = 4))
    #########################
    #SAFT ###################
    SrvMSG_ML = BitArray(uint=0, length = 9) # Length
    SrvMSG = SrvMSG_ECC + SrvMSG_TSEID + SrvMSG_ML
    layer3(SrvMSG,'0x8',BitArray('0b0010', length = 4))
    #########################
    #COT ###################
    SrvMSG_ML = BitArray(uint=2, length = 9) # TBF
    SrvMSG_SID = BitArray(uint=SChanID,length=14) # Channel ID 
    SrvMSG_CA = BitArray('0b0', length = 1) # No CA
    SrvMSG_SA = BitArray('0b1', length = 1) # Service is available
    SrvMSG = SrvMSG_ECC + SrvMSG_TSEID + SrvMSG_ML + SrvMSG_SID + SrvMSG_CA + SrvMSG_SA
    layer3(SrvMSG,'0x8',BitArray('0b0000', length = 4))

    L3_SUP+=1



if __name__ == '__main__':

    BICs = (['0x135e', '0x74a6', '0xa791', '0xc875'])
    #global L3_SC
        
    Framecnt = 0
    iBusID = 0x065A
    busNumber = 23
    offset = 0
    busstr = "23"
    destination = "FNORDWEG"
    sequenceNumber = 0
    SeChanId = 56

    ba = bitarray()

        # Static Variables
        #self.SeCh_data = BitArray(length=8*304) # max 304 bytes, see 8.3.1
        #self.LMCh_data = BitArray(length=8*256) # max 256 bytes

        #self.lmch_blocknumber = 0

        #self.scramble_table = BitArray('0b10101111101010101000000101001010111100101110111000000111001110100100111101011101010001001000011001110000101111011011001101000011101111000011111111100000111101111100010111001100100000100101001110110100011110011111001101100010101001000111000110110101011100010011000100010000') 
    LMCh_ident = BitArray('0x000001',length=24)
    LMCh_iBusID = BitArray(uint=iBusID, length=16)
    
    LMCh_type = BitArray('0x2c',length = 8)
    LMCh_sequenceNumber = BitArray(uint=sequenceNumber,length = 8)
    LMCh_fd = BitArray('0xfd0b',length = 16)
    LMCh_BusNo = BitArray(uint = busNumber, length=16)
    LMCh_00fffff = BitArray('0x00ffff',length=24)
    LMCh_lineNumberLength = BitArray('0x02',length=8)
    LMCh_lineNumberASCII = Bits(bytes=busstr)
    LMCh_000129 = BitArray('0x000129',length=24)
    LMCh_ef = BitArray('0xef',length=8)
    LMCh_strange = BitArray(uint=(0x20+(3*sequenceNumber)),length=8)
    LMCh_destinationString = Bits(bytes=destination)
    LMCh_25 = BitArray(uint=0x2580+sequenceNumber,length=16)
    LMCh_46 = BitArray(uint=0x4600+sequenceNumber,length=16)
    LMCh_0f = BitArray('0x0f810000',length=32)
    LMCh_offset = BitArray(uint=offset, length=8)
    LMCh_v3 = BitArray('0x0376330001',length=40)

    LMCh_fullLength = BitArray(uint=19+(len(destination))+16,length=16)
    LMCh_lengthTillEnd1 = BitArray(uint=2+(len(destination)),length=8)
    LMCh_lengthTillEnd2 = BitArray(uint=(len(destination)),length=8)

    LMCh_1 = LMCh_ident + LMCh_iBusID + LMCh_fullLength + LMCh_type + LMCh_sequenceNumber + LMCh_fd + LMCh_BusNo + LMCh_sequenceNumber + LMCh_00fffff + LMCh_lineNumberLength \
             + LMCh_lineNumberASCII + LMCh_000129 + LMCh_sequenceNumber + LMCh_ef + LMCh_lengthTillEnd1 + LMCh_strange + LMCh_lengthTillEnd2 + LMCh_destinationString \
             + LMCh_25 + LMCh_46 + LMCh_0f + LMCh_offset + LMCh_v3
    #print(str(LMCh_1))

    LMCh_2 = LMCh_ident + LMCh_iBusID + BitArray('0x0024',length=16) + BitArray('0x124e0000760f000a7613000076180000730a8000730b800076141113730a902f730b8739',length=8*24)
    #print(str(LMCh_2))
   


    # Time Message: Show on Display 1 on line 1 and 2 destination 0 with times 23min and 42min
    # Length of time-message is 0x30
    LMCh_time_length =  BitArray('0x0030',length = 16)
    LMCh_time =         BitArray('0b000000000001011100100000001010100100000000101010',length=48)
    LMCH_zerotime =     BitArray('0b111000001110000011100000111000001110000011100000',length=48)
    LMCH_lastzerotime = BitArray('0b111000001110000011100000111000001110000011101011',length=48)
    LMCh_3 = LMCh_time_length + LMCh_time + LMCH_zerotime + LMCH_zerotime + LMCH_zerotime + LMCH_zerotime + LMCH_zerotime + LMCH_zerotime + LMCH_lastzerotime
    #print(str(LMCh_1))
    while(FrameCnt < 24):
        if FrameCnt == 0:
            #print(FrameCnt)
            blockMessage(FrameCnt, 2,SeChanId)
            layer4_LMch(LMCh_1,SeChanId)
            layer4_LMch(LMCh_2,SeChanId)
            while(L3_SC < 190):
                fillFrame(SeChanId)
        else:
            blockMessage(FrameCnt, 1,SeChanId)
            layer4_LMch(LMCh_3,SeChanId)
            while(L3_SC < 190):
                fillFrame(SeChanId)
        FrameCnt += 1

        L3_SUP = 0
        L3_SC = 0


    
    L3_SC = 0
