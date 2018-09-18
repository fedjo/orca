# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Spectrum Sense
# Generated: Wed Sep 12 18:59:30 2018
##################################################

from gnuradio import blocks
from gnuradio import fft
from gnuradio import gr
from gnuradio import uhd
from gnuradio.fft import window
from gnuradio.filter import firdes
import time


class spectrum_sense(gr.hier_block2):

    def __init__(self):
        gr.hier_block2.__init__(
            self, "Spectrum Sense",
            gr.io_signature(1, 1, gr.sizeof_gr_complex),
            gr.io_signature(0, 0, 0),
        )

        ##################################################
        # Variables
        ##################################################

        ##################################################
        # Message Queues
        ##################################################
        self.sense_sink_queue = gr.msg_queue(2)

        ##################################################
        # Blocks
        ##################################################
        self.fft_vxx_0 = fft.fft_vcc(1024, True, (window.blackmanharris(1024)), True, 1)
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_gr_complex*1, 1024)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, 1024)
        self.blocks_nlog10_ff_0 = blocks.nlog10_ff(10, 1, 0)
        #self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_float*1, 'output.txt', False)
        #self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_float*1, self.sink_queue, True)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(1)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.blocks_nlog10_ff_0, 0))
        #self.connect((self.blocks_nlog10_ff_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blocks_nlog10_ff_0, 0), (self.blocks_message_sink_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.blocks_vector_to_stream_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_vector_to_stream_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.blocks_stream_to_vector_0, 0))
