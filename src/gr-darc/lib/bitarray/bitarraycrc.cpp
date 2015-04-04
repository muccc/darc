/***************************************************************************
*                         Arrays of Arbitrary Bit Length
*
*   File    : bitarraycrc.cpp
*   Purpose : 
*
*   Author  : 
*   Date    : 
*
****************************************************************************
*   HISTORY
*
*
****************************************************************************
*
* <insert GNU license here>
*
***************************************************************************/

/***************************************************************************
*                             INCLUDED FILES
***************************************************************************/
#include <iostream>
#include <climits>
#include "bitarraycrc.h"
using namespace std;

/***************************************************************************
*                                 MACROS
***************************************************************************/

/***************************************************************************
*                                 METHODS
***************************************************************************/

/***************************************************************************
*   Method     : 
*   Description: 
*   Parameters : 
*   Effects    : 
*   Returned   : 
***************************************************************************/
void
bit_array_crc(bit_array_c &crc, 
            const bit_array_c &input, 
            const bit_array_c &polynom, 
            const bit_array_c &code)
{
    // TODO Check for Codelength and CRC Len to be polynomLen-1

    // Concatenate input and code to be tested to a tmp bit array
    bit_array_c tmp(input.Size()+crc.Size());
    tmp.Copy(0, input, 0, input.Size());
    tmp.Copy(input.Size(), code, 0, code.Size());

    /* Step through input data
     * if a bit is true, XOR the polynom to the tmp bit array
     */
    for(unsigned int cnt=0; cnt<input.Size(); cnt++)
    {
        if(tmp[cnt])
        {
            for(unsigned int pos=0; pos<polynom.Size(); pos++)
            {
                tmp(cnt+pos) = tmp[cnt+pos] ^ polynom[pos];
            }
        }
    }
    // Copy to target BitArray
    crc.Copy(0, tmp, input.Size(), crc.Size());
}
