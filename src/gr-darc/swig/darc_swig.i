/* -*- c++ -*- */

#define DARC_API

%include "gnuradio.i"			// the common stuff

//load generated python docstrings
%include "darc_swig_doc.i"

%{
#include "darc/layer2.h"
#include "darc/layer2_sync.h"
#include "darc/layer2_format.h"
%}


%include "darc/layer2.h"
GR_SWIG_BLOCK_MAGIC2(darc, layer2);
%include "darc/layer2_sync.h"
GR_SWIG_BLOCK_MAGIC2(darc, layer2_sync);
%include "darc/layer2_format.h"
GR_SWIG_BLOCK_MAGIC2(darc, layer2_format);
