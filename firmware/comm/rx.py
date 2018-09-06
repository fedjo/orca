#!/usr/bin/env python2
# -*- coding: utf-8 -*-
##################################################
# GNU Radio Python Flow Graph
# Title: Rx File
# Generated: Tue Sep  4 18:12:45 2018
##################################################

from gnuradio import blocks
from gnuradio import digital
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.filter import firdes
from grc_gnuradio import blks2 as grc_blks2


class rx_path(gr.hier_block2):

    def __init__(self, samp_rate, freq, code1, code2):
        gr.hier_block2.__init__(self, "Receiving Rx",
                                gr.io_signature(0, 0, 0), # Null signature
                                gr.io_signature(0, 0, 0))

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 64000
        self.freq = freq = 1.24e09
        self.code1 = code1 = '010110011011101100010101011111101001001110001011010001101010001'
        self.code2 = code2 = '11011010110111011000110011110101100010010011110111'

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
        self.uhd_usrp_source_0.set_gain(10, 0)
        self.uhd_usrp_source_0.set_bandwidth(100e06, 0)
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
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, 'out.txt', False)
        self.blocks_file_sink_0.set_unbuffered(True)
        self.blks2_packet_decoder_0 = grc_blks2.packet_demod_b(grc_blks2.packet_decoder(
        		access_code=code1,
        		threshold=-1,
        		callback=lambda ok, payload: self.blks2_packet_decoder_0.recv_pkt(ok, payload),
        	),
        )

        ##################################################
        # Connections
        ##################################################
        self.connect((self.blks2_packet_decoder_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.digital_dxpsk_demod_1, 0), (self.blks2_packet_decoder_0, 0))
        self.connect((self.uhd_usrp_source_0, 0), (self.digital_dxpsk_demod_1, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.uhd_usrp_source_0.set_samp_rate(self.samp_rate)

    def get_freq(self):
        return self.freq

    def set_freq(self, freq):
        self.freq = freq
        self.uhd_usrp_source_0.set_center_freq(self.freq, 0)
