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

#include <gnuradio/io_signature.h>
#include "darc_constants.h"
#include "layer2_sync_impl.h"

namespace gr {
  namespace darc {

    layer2_sync::sptr
    layer2_sync::make(bool log, bool debug)
    {
      return gnuradio::get_initial_sptr
        (new layer2_sync_impl(log, debug));
    }

    /*
     * The private constructor
     */
    layer2_sync_impl::layer2_sync_impl(bool log, bool debug)
      : gr::block("layer2_sync",
              gr::io_signature::make(1, 1, sizeof(char)),
              gr::io_signature::make(1, 1, 36*sizeof(char))),
      log(log),
      debug(debug)
    {
    }

    /*
     * Our virtual destructor.
     */
    layer2_sync_impl::~layer2_sync_impl()
    {
    }

        void
    layer2_sync_impl::forecast (int noutput_items, gr_vector_int &ninput_items_required)
    {
        ninput_items_required[0] = BLOCK_LENGTH*(noutput_items+1);
    }

    int
    layer2_sync_impl::general_work (int noutput_items,
                       gr_vector_int &ninput_items,
                       gr_vector_const_void_star &input_items,
                       gr_vector_void_star &output_items)
    {
        /**********************************
        TODO:
        Implement Search Window (2Bits up/dwn)
        What shall we do if in Sync, but no BIC found in search Window? --> To get a flull frame!
        **********************************/
        const char *in = (const char *) input_items[0];
        char *out = (char *) output_items[0];

        int _noutput_items = 0;
        unsigned short bic = 0x00;
        unsigned int items_consumed = 0;

        dout << "ninput_items: " << ninput_items[0] << std::endl;
        dout << "noutput_items: " << noutput_items << std::endl;
        
        // Take care to have enough bits to form a packet
        while(items_consumed<(ninput_items[0]-BLOCK_LENGTH))
        {
          bic=(bic<<1)|in[items_consumed]; // BIC Input shift register
          
          // BICs = (['0x135e', '0x74a6', '0xa791', '0xc875'])
          if (   0x135e == bic
              || 0x74a6 == bic
              || 0xa791 == bic
              || 0xc875 == bic )
          {      
             //dout << "[DBG] BIC found" << std::endl;

             // Assign L2 Body
             unsigned int index = _noutput_items*(BLOCK_LENGTH/8);

             out[index++] = (char)((bic>>8) & 0xFF);
             out[index++] = (char)(bic & 0xFF);
             for(unsigned int cnt=0; cnt<L2_BODY_LEN; cnt++)
             {
                // TODO put L2data into char array instead of short
                // TODO try using memcpy for this
                unsigned short idx = (cnt / 16);
                l2data[idx] = (l2data[idx]<<1)|in[++items_consumed];

                if(0 != cnt && 15 == cnt % 16)
                {
                  /* 
                   * Descramble with Scramble Table
                   * ETSI EN 300 751 7.3.2.6
                   */
                  l2data[idx] = l2data[idx] ^ scramble_table[idx];
                  out[index+idx*2] = (char)((l2data[idx]>>8) & 0xFF);
                  out[index+(idx*2)+1] = (char)(l2data[idx] & 0xFF);
                }
             }
             _noutput_items++;

             if(noutput_items <= _noutput_items)
             {
              dout << "Reached max noutput_items" << std::endl;
              break;
             }
          }
          else
            items_consumed++; //if no BIC found, take one more bit
        }
        dout << "consumed_items: " << _noutput_items * BLOCK_LENGTH << std::endl;
        dout << "_noutput_items: " << _noutput_items << std::endl;
        dout << std::endl;
        consume_each(items_consumed);
        return _noutput_items;
    }

  } /* namespace darc */
} /* namespace gr */
