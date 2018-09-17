#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Pu Detect Channel
# Generated: Thu Sep 13 15:16:57 2018
##################################################

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from grc_gnuradio import blks2 as grc_blks2
from optparse import OptionParser
import time
import sys
import os

class detect_pu(gr.hier_block2):

    def __init__(self, freq, bandwidth, samp_rate, code1):
        gr.hier_block2.__init__(
            self, "Detect Primary Users",
            gr.io_signature(0, 0, 0),
            gr.io_signature(0, 0, 0),
        )

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate
        self.code1 = code1 = '010110011011101100010101011111101001001110001011010001101010001'
        self.freq = freq
        self.bandwidth = bandwidth


        print("Rate: {}, Freq: {}, Band: {}".format(samp_rate, freq,bandwidth))
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
        self.uhd_usrp_source_0.set_center_freq(freq, 0)
        self.uhd_usrp_source_0.set_gain(60, 0)
        self.uhd_usrp_source_0.set_bandwidth(bandwidth, 0)
        self.digital_dxpsk_demod_1 = digital.dbpsk_demod(
        	samples_per_symbol=2,
        	excess_bw=0.35,
        	freq_bw=6.28/100.0,
        	phase_bw=6.28/100.0,
        	timing_bw=6.28/100.0,
        	mod_code="gray",
        	verbose=False,
        	log=False
        )
        # self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, fname, False)
        # self.blocks_file_sink_0.set_unbuffered(True)
        self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*1, self.sink_queue, True)
        self.blks2_packet_decoder_0 = grc_blks2.packet_demod_b(grc_blks2.packet_decoder(
        		access_code=code1,
        		threshold=-1,
        		callback=lambda ok, payload: self.blks2_packet_decoder_0.recv_pkt(ok, payload),
        	),
        )

        ##################################################
        # Connections
        ##################################################
        # self.connect((self.blks2_packet_decoder_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blks2_packet_decoder_0, 0), (self.blocks_message_sink_0, 0))
        self.connect((self.digital_dxpsk_demod_1, 0), (self.blks2_packet_decoder_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.digital_dxpsk_demod_1, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_code1(self):
        return self.code1

    def set_code1(self, code1):
        self.code1 = code1

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.uhd_usrp_source_0.set_center_freq(self.freq, 0)

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth
        self.uhd_usrp_source_0.set_bandwidth(self.bandwidth, 0)
