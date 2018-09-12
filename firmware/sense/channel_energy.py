#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Orig Single Channel
# Generated: Fri Sep  7 16:29:33 2018
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
import time
import sys
import avg
import transmit_busy_tone as busy


class orig_single_channel(gr.top_block):

    def __init__(self,c_freq, bandwidth):
        # gr.top_block.__init__(self, "Orig Single Channel")
        gr.hier_block2.__init__(self, "Orig Single Channel",
                                gr.io_signature(0, 0, 0), # Null signature
                                gr.io_signature(0, 0, 0))

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 64000
        self.c_freq = c_freq
        self.bandwidth = bandwidth

        ##################################################
        # Message Queues
        ##################################################
        self.sink_queue = gr.msg_queue(2)

        ##################################################
        # Blocks
        ##################################################
        self.uhd_usrp_source_0 = uhd.usrp_source(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.uhd_usrp_source_0.set_samp_rate(samp_rate)
        self.uhd_usrp_source_0.set_center_freq(c_freq, 0)
        self.uhd_usrp_source_0.set_gain(60, 0)
        self.uhd_usrp_source_0.set_bandwidth(bandwidth, 0)
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

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_c_freq(self):
        return self.c_freq

    def set_c_freq(self, c_freq):
        self.c_freq = c_freq
        self.uhd_usrp_source_0.set_center_freq(self.c_freq, 0)

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth
        self.uhd_usrp_source_0.set_bandwidth(self.bandwidth, 0)


def calc_energy(c_freq, bandwidth, top_block_cls=orig_single_channel, options=None):
    tb = top_block_cls(c_freq, bandwidth)
    tb.start()
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()
    mean = avg.find_average("output.txt")
    return mean


