/* -*- c++ -*- */
/* 
 * Copyright 2015 <+YOU OR YOUR COMPANY+>.
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <stdio.h>
#include <iostream>
#include <stdlib.h>
#include <fstream>
#include <gnuradio/io_signature.h>
#include "darc_constants.h"
#include "layer2_format_impl.h"

#include "bitarray/bitarray.h"
#include "bitarray/bitarraycrc.h"


using namespace std;

namespace gr {
  namespace darc {

    layer2_format::sptr
    layer2_format::make(bool log, 
                        bool debug, 
                        bool crc, 
                        bool repair, 
                        unsigned char errorwidth)
    {
      return gnuradio::get_initial_sptr
        (new layer2_format_impl(log, debug,crc,repair, errorwidth));
    }

    /*
     * The private constructor
     */
    layer2_format_impl::layer2_format_impl(bool log, 
                                            bool debug, 
                                            bool crc, 
                                            bool repair,
                                            unsigned char errorwidth)
      : gr::block("layer2_format",
              gr::io_signature::make(1, 1, 36*sizeof(char)),
              gr::io_signature::make(1, 1, 24*sizeof(char))),
      log(log),
      debug(debug),
      m_crc(crc),
      m_repair(repair),
      m_errorwidth(errorwidth)
    {
      if(m_repair)
      {
        syndrome_generator(false); // Do not generate syndrome export file
      }

      m_stats_total = 0;
      m_stats_crcok = 0;
      m_stats_repaired = 0;
    }

    /*
     * Our virtual destructor.
     */
    layer2_format_impl::~layer2_format_impl()
    {
    }

    void
    layer2_format_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
       ninput_items_required[0] = noutput_items+1;
    }

    bool
    layer2_format_impl::crc14 (const bit_array_c &data,
                                const bit_array_c &crc)
    {
      /* x^14 + x^11 + x^2 +1 (1001 0000 0000 101|0)*/
      unsigned char *poly = new unsigned char[2];
      poly[0] = 0x90;
      poly[1] = 0x0A;

      bit_array_c result(14);
      bit_array_c polynom(poly, 15);

      bit_array_crc(result, data, polynom, crc);

      // Check if result is zero, if yes, CRC was ok
      bit_array_c zero(14);
      if(zero == result)
      {
        return true;
      }
      return false;
    }

    void
    layer2_format_impl::crc82(bit_array_c &result, 
                              const bit_array_c &data, 
                              const bit_array_c &code)
    {
      /* Chapter 11.1
       * 10000110 00010001 10000000 00100010 
       * 00100000 00100010 10000000 00101000
       * 10000000 10000010 001
       */
      unsigned char *poly = new unsigned char[11];
      poly[0] = 0x86;
      poly[1] = 0x11;
      poly[2] = 0x80;
      poly[3] = 0x22;
      poly[4] = 0x20;
      poly[5] = 0x22;
      poly[6] = 0x80;
      poly[7] = 0x28;
      poly[8] = 0x80;
      poly[9] = 0x82;
      poly[10] = 0x20;
      bit_array_c polynom(poly, 83);

      bit_array_crc(result, data, polynom, code);
    }

    int
    layer2_format_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
        const char *in = (const char *) input_items[0];
        char *out = (char *) output_items[0];

        unsigned int _items_consumed = 0;
        unsigned int _noutput_items = 0;

        while(_items_consumed<1)
        {          
          bool success = false;

          bit_array_c block((const unsigned char*)&in[0], \
                              BLOCK_LENGTH);

          unsigned short bic = in[0]<<8 | in[1];
          if( 0xc875 != bic ) // Ignore Parity BIC
          {             
            m_stats_total++;

            if(!m_crc)
            {
              success = true;
            }
            else
            {
              bit_array_c data(L2_INFO_LEN);
              data.Copy(0, block, BIC_LEN, L2_INFO_LEN);
              bit_array_c crc(L2_CRC_LEN);
              crc.Copy(0, block, BIC_LEN+L2_INFO_LEN, L2_CRC_LEN);

              if(crc14(data, crc))
              {
                m_stats_crcok++;
                success = true;
              }
              else if(m_repair)
              {
                bit_array_c data_and_crc(L2_INFO_LEN+L2_CRC_LEN);
                data_and_crc.Copy(0, block, BIC_LEN, L2_INFO_LEN+L2_CRC_LEN);
                
                bit_array_c parity(L2_PARITY_LEN);
                parity.Copy(0, block, BIC_LEN+L2_INFO_LEN+L2_CRC_LEN, L2_PARITY_LEN);

                bit_array_c result(L2_PARITY_LEN);
                crc82(result, data_and_crc, parity);

                for(unsigned int x = 0; x < m_paritylist.size(); x++)
                { // Searching for the parity value
                  if(result == *m_paritylist[x])
                  { 
                    // Found the right value in the parity list,
                    // applying syndrome
                    data_and_crc = data_and_crc ^ *m_syndromelist[x];

                    // Checking CRC again
                    data.Copy(0, data_and_crc, 0, L2_INFO_LEN);
                    crc.Copy(0, data_and_crc, L2_INFO_LEN, L2_CRC_LEN);
                    if(crc14(data, crc))
                    {
                      m_stats_repaired++;
                      success = true;
                      block.Copy(BIC_LEN, data_and_crc, 0, L2_INFO_LEN+L2_CRC_LEN);
                    }
                  }
                }
              }
            }

            if(success)
            {
              memcpy(&out[0], (block.GetArray()), ((BIC_LEN+L2_INFO_LEN)/8)*sizeof(char));
            }
            else
            {
              // Providing packet informatio to the other layers anyway
              memcpy(&out[0], (block.GetArray()), ((BIC_LEN+L2_INFO_LEN)/8)*sizeof(char));
              //memset(&out[0], 0, ((BIC_LEN+L2_INFO_LEN)/8)*sizeof(char));
            }
            _noutput_items++;

            if( m_stats_total%100000 == 0)
            {
              int crc_rate = (m_stats_crcok*100)/m_stats_total;
              int repair_rate = (m_stats_repaired*100)/(m_stats_total-m_stats_crcok);
              lout << "[Log][L2 Stats]";
              lout << " CRC OK: " << crc_rate << "%";
              lout << " Repaired: " << repair_rate << "%";
              lout << " TotalRx: " << m_stats_total << endl;
            }
          }
          _items_consumed++;                    
        }

        consume_each (_items_consumed);
        // Tell runtime system how many output items we produced.
        return _noutput_items;
    }

    void 
    layer2_format_impl::syndrome_generator(bool generateFile)
    {
      ofstream fhandle;
      if(generateFile)
      {        
        fhandle.open("/home/chris/Desktop/mysyndrome");    
      }  

      bit_array_c data(L2_INFO_LEN + L2_CRC_LEN); //190
      bit_array_c parity(L2_PARITY_LEN); //82
      bit_array_c code(L2_PARITY_LEN); // stays zero

      bit_array_c pattern(m_errorwidth);
      bit_array_c counter(m_errorwidth);

      cout << "Generating syndrome table";
      for(unsigned char bits=1; bits<=m_errorwidth; bits++)
      {
        cout << ".";
        // Create bit error pattern
        // First and last bit of pattern is always set
        // otherwise the pattern would be the same as shorter patterns 
        // looked before
        // Bits in between are simply counted up
        pattern.ClearAll();
        pattern.SetBit(0);
        pattern.SetBit(bits-1);

        counter.ClearAll();

        for(unsigned int cnt=0; cnt<pow(2,bits-2); cnt++)
        {
          if(bits > 2)
          {  
            counter.FromInt(cnt);
            pattern.Copy(1, counter, 0, bits-2);            
          }

          // Iterate pattern through every 
          // possible position in datastream
          for(unsigned char pos=0; pos<=data.Size()-bits; pos++)
          {
            data.ClearAll();
            data.Copy(pos, pattern, 0, bits);

            // Calculate CRC82
            crc82(parity, data, code);

            // Storing parity/syndrome list on the heap
            m_paritylist.push_back(new bit_array_c(parity));
            m_syndromelist.push_back(new bit_array_c(data));

            if(generateFile)
            {
              //dump to file
              parity.Dump(fhandle);
              fhandle << "   ";
              data.Dump(fhandle);
              fhandle << std::endl;
            }
          }
        }
      }
      fhandle.close();
      cout << "done" << endl;
    }

  } /* namespace darc */
} /* namespace gr */
