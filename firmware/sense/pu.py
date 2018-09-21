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

    def __init__(self, code1):
        gr.hier_block2.__init__(
            self, "Detect Primary Users",
            gr.io_signature(1, 1, gr.sizeof_gr_complex),
            gr.io_signature(0, 0, 0),
        )

        ##################################################
        # Variables
        ##################################################
        self.code1 = code1 = '010110011011101100010101011111101001001110001011010001101010001'
        self.probe_value = probe_value = 0

        ##################################################
        # Message Queues
        ##################################################
        self.pu_sink_queue = gr.msg_queue(2)


        ##################################################
        # Blocks
        ##################################################
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
        self.blks2_packet_decoder_0 = grc_blks2.packet_demod_b(grc_blks2.packet_decoder(
        		access_code=code1,
        		threshold=-1,
        		callback=lambda ok, payload: self.blks2_packet_decoder_0.recv_pkt(ok, payload),
        	),
        )

        ## Sinks ##
        #
        #self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, 'output.out', True)
        #self.blocks_file_sink_0.set_unbuffered(True)
        self.blocks_message_sink_0 = blocks.message_sink(gr.sizeof_char*1, self.pu_sink_queue, True)
        self.blocks_probe_signal_0 = blocks.probe_signal_b()
        self.blocks_probe_signal_vector_0 = blocks.probe_signal_vb(1)

        ##################################################
        # Connections
        ##################################################
        #self.connect((self.blks2_packet_decoder_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.blks2_packet_decoder_0, 0), (self.blocks_message_sink_0, 0))
        self.connect((self.blks2_packet_decoder_0, 0), (self.blocks_probe_signal_0, 0))
        self.connect((self.blks2_packet_decoder_0, 0), (self.blocks_probe_signal_vector_0, 0))

        self.connect((self.digital_dxpsk_demod_1, 0), (self.blks2_packet_decoder_0, 0))
        self.connect(self, (self.digital_dxpsk_demod_1, 0))



        def _probe_vector_value_probe():
            while True:
                val = self.blocks_probe_signal_0.level()
                try:
                    self.set_probe_value(val)
                except AttributeError:
                    pass
                time.sleep(1.0/10000)
        _probe_vector_value_thread = threading.Thread(target=_probe_vector_value_probe)
        _probe_vector_value_thread.daemon = True
        _probe_vector_value_thread.start()


    def get_probe_value(self):
        return self.probe_value


    def set_probe_value(self, probe_value):
        self.probe_value = probe_value
