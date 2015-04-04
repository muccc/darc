


#ifndef DARC_CONSTANTS_H
#define DARC_CONSTANTS_H


#define dout debug && std::cout
#define lout log && std::cout

/* Protocol Constants, Lengths given in Bit */
/* Layer 2 */
#define L2_INFO_LEN     176
#define L2_CRC_LEN      14
#define L2_PARITY_LEN   82
#define L2_BODY_LEN     272   /* 272 */
#define BIC_LEN         16
#define BLOCK_LENGTH    288       /* 288 */


static const unsigned int bic[4] = {0x135e,0x74a6,0xa791,0xc875};

static const unsigned short scramble_table[17] = { 0xAFAA,
                                               0x814A,
                                               0xF2EE,
                                               0x073A,
                                               0x4F5D,
                                               0x4486,
                                               0x70BD,
                                               0xB343,
                                               0xBC3F,
                                               0xE0F7,
                                               0xC5CC,
                                               0x8253,
                                               0xB479,
                                               0xF362,
                                               0xA471,
                                               0xB571,
                                               0x3110};



#endif // DARC_CONSTANTS_H