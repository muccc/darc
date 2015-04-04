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

#ifndef INCLUDED_DARC_LAYER2_FORMAT_IMPL_H
#define INCLUDED_DARC_LAYER2_FORMAT_IMPL_H

#include <darc/layer2_format.h>

#include "bitarray/bitarray.h"

namespace gr {
  namespace darc {

    class layer2_format_impl : public layer2_format
    {
     private:
      bool log;
      bool debug;
      bool m_crc;
      bool m_repair;
      unsigned char m_errorwidth;

      std::vector<bit_array_c*> m_paritylist;
      std::vector<bit_array_c*> m_syndromelist;

      // Performance logging
      unsigned long m_stats_total;
      unsigned long m_stats_crcok;
      unsigned long m_stats_repaired;

     public:
      layer2_format_impl(bool log, 
                          bool debug, 
                          bool crc, 
                          bool repair, 
                          unsigned char errorwidth);
      ~layer2_format_impl();

      // Where all the action really happens
      void forecast (int noutput_items, gr_vector_int &ninput_items_required);

      int general_work(int noutput_items,
		       gr_vector_int &ninput_items,
		       gr_vector_const_void_star &input_items,
		       gr_vector_void_star &output_items);

      bool crc14(const bit_array_c &data, 
                  const bit_array_c &crc);
      void crc82(bit_array_c &result, 
                  const bit_array_c &data, 
                  const bit_array_c &code);

      void syndrome_generator(bool generateFile);
    };

  } // namespace darc
} // namespace gr

#endif /* INCLUDED_DARC_LAYER2_FORMAT_IMPL_H */

