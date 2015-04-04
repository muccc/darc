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
#include "layer2_impl.h"
#include "layer2_sync_impl.h"
#include "layer2_format_impl.h"

namespace gr {
  namespace darc {

    layer2::sptr
    layer2::make(bool log, 
                  bool debug, 
                  bool crc, 
                  bool repair,
                  unsigned char errorwidth)
    {
      return gnuradio::get_initial_sptr
        (new layer2_impl(log, debug, crc, repair, errorwidth));
    }

    /*
     * The private constructor
     */
    layer2_impl::layer2_impl(bool log, 
                              bool debug, 
                              bool crc, 
                              bool repair,
                              unsigned char errorwidth)
      : gr::hier_block2("layer2",
              gr::io_signature::make(1, 1, sizeof(char)),
              gr::io_signature::make(1, 1, 24*sizeof(char)))
    {
      gr::darc::layer2_sync::sptr layer2_sync(gr::darc::layer2_sync::make(log, debug));
      gr::darc::layer2_format::sptr layer2_format(gr::darc::layer2_format::make(log,
                                                                                debug,
                                                                                crc,
                                                                                repair,
                                                                                errorwidth));


        connect(self(), 0, layer2_sync, 0);
        connect(layer2_sync, 0, layer2_format, 0);
        connect(layer2_format, 0, self(), 0);
    }

    /*
     * Our virtual destructor.
     */
    layer2_impl::~layer2_impl()
    {
    }


  } /* namespace darc */
} /* namespace gr */

