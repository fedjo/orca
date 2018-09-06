#!/usr/bin/env python
#
# Copyright 2005,2007,2011 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, eng_notation
from gnuradio import blocks
from gnuradio import audio
from gnuradio import filter
from gnuradio import fft
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from optparse import OptionParser
import sys
import math
import struct
import threading
from datetime import datetime
import time

sys.stderr.write("Warning: this may have issues on some machines+Python version combinations to seg fault due to the callback in bin_statitics.\n\n")

class tune(gr.feval_dd):
    """
    This class allows C++ code to callback into python.
    """
    def __init__(self, tb):
        gr.feval_dd.__init__(self)
        self.tb = tb

    def eval(self, ignore):
        """
        This method is called from blocks.bin_statistics_f when it wants
        to change the center frequency.  This method tunes the front
        end to the new center frequency, and returns the new frequency
        as its result.
        """

        try:
            # We use this try block so that if something goes wrong
            # from here down, at least we'll have a prayer of knowing
            # what went wrong.  Without this, you get a very
            # mysterious:
            #
            #   terminate called after throwing an instance of
            #   'Swig::DirectorMethodException' Aborted
            #
            # message on stderr.  Not exactly helpful ;)

            new_freq = self.tb.set_next_freq()

            # wait until msgq is empty before continuing
            while(self.tb.msgq.full_p()):
                #print "msgq full, holding.."
                time.sleep(0.1)

            return new_freq

        except Exception, e:
            print "tune: Exception: ", e


class parse_msg(object):
    def __init__(self, msg):
        self.center_freq = msg.arg1()
        self.vlen = int(msg.arg2())
        assert(msg.length() == self.vlen * gr.sizeof_float)

        # FIXME consider using NumPy array
        t = msg.to_string()
        self.raw_data = t
        self.data = struct.unpack('%df' % (self.vlen,), t)


class sense_path(gr.hier_block2):

    def __init__(self, channel_bandwidth, min_freq, max_freq, samp_rate,
                 tune_delay, dwell_delay, gain):
        # gr.top_block.__init__(self)
        gr.hier_block2.__init__(self, "Spectrum Sense",
                                gr.io_signature(0, 0, 0), # Null signature
                                gr.io_signature(0, 0, 0))
        self.gain = gain
        self.channel_bandwidth = channel_bandwidth
        self.squelch_threshold = 0

        self.min_freq = min_freq
        self.max_freq = max_freq

        print "Hi i am scanning the spectrum between freqs ", min_freq, " and ", max_freq
        if self.min_freq > self.max_freq:
            # swap them
            self.min_freq, self.max_freq = self.max_freq, self.min_freq



        # build graph
        self.u = uhd.usrp_source(device_addr="",stream_args=uhd.stream_args('fc32'))

        # Set the subdevice spec

        # Set the antenna



        self.u.set_samp_rate(samp_rate)
        self.usrp_rate = usrp_rate = self.u.get_samp_rate()

        self.lo_offset = 0

        self.fft_size = int(self.usrp_rate/self.channel_bandwidth)


        s2v = blocks.stream_to_vector(gr.sizeof_gr_complex, self.fft_size)

        mywindow = filter.window.blackmanharris(self.fft_size)
        ffter = fft.fft_vcc(self.fft_size, True, mywindow, True)
        power = 0
        for tap in mywindow:
            power += tap*tap

        c2mag = blocks.complex_to_mag_squared(self.fft_size)

        # FIXME the log10 primitive is dog slow
        #log = blocks.nlog10_ff(10, self.fft_size,
        #                       -20*math.log10(self.fft_size)-10*math.log10(power/self.fft_size))

        # Set the freq_step to 75% of the actual data throughput.
        # This allows us to discard the bins on both ends of the spectrum.

        self.freq_step = self.nearest_freq((0.75 * self.usrp_rate), self.channel_bandwidth)
        self.min_center_freq = self.min_freq + (self.freq_step/2)
        nsteps = math.ceil((self.max_freq - self.min_freq) / self.freq_step)
        self.max_center_freq = self.min_center_freq + (nsteps * self.freq_step)

        self.next_freq = self.min_center_freq

        tune_delay  = max(0, int(round(tune_delay * usrp_rate / self.fft_size)))  # in fft_frames
        dwell_delay = max(1, int(round(dwell_delay * usrp_rate / self.fft_size))) # in fft_frames

        self.msgq = gr.msg_queue(1)
        self._tune_callback = tune(self)        # hang on to this to keep it from being GC'd
        stats = blocks.bin_statistics_f(self.fft_size, self.msgq,self._tune_callback, tune_delay,dwell_delay)

        # FIXME leave out the log10 until we speed it up
	    #self.connect(self.u, s2v, ffter, c2mag, log, stats)
        self.connect(self.u, s2v, ffter, c2mag, stats)

        self.set_gain(gain)
        print "gain =", gain

    def set_next_freq(self):
        target_freq = self.next_freq
        self.next_freq = self.next_freq + self.freq_step
        if self.next_freq >= self.max_center_freq:
            self.next_freq = self.min_center_freq

        if not self.set_freq(target_freq):
            print "Failed to set frequency to", target_freq
            sys.exit(1)

        return target_freq


    def set_freq(self, target_freq):
        """
        Set the center frequency we're interested in.
        Args:
            target_freq: frequency in Hz
        @rypte: bool
        """

        r = self.u.set_center_freq(uhd.tune_request(target_freq, rf_freq=(target_freq + self.lo_offset),rf_freq_policy=uhd.tune_request.POLICY_MANUAL))
        if r:
            return True

        return False

    def set_gain(self, gain):
        self.u.set_gain(gain, 0)

    def nearest_freq(self, freq, channel_bandwidth):
        freq = round(freq / channel_bandwidth, 0) * channel_bandwidth
        return freq

def sense(flowgraph):

    def bin_freq(i_bin, center_freq):
        #hz_per_bin = tb.usrp_rate / tb.fft_size
        freq = center_freq - (tb.usrp_rate / 2) + (tb.channel_bandwidth * i_bin)
        #print "freq original:",freq
        #freq = nearest_freq(freq, tb.channel_bandwidth)
        #print "freq rounded:",freq
        return freq

    res = False
    bin_start = int(tb.fft_size * ((1 - 0.75) / 2))
    bin_stop = int(tb.fft_size - bin_start)
    timestamp = 0
    centerfreq = 0
    while 1:
        # Get the next message sent from the C++ code (blocking call).
        # It contains the center frequency and the mag squared of the fft
        m = parse_msg(tb.msgq.delete_head())

        # m.center_freq is the center frequency at the time of capture
        # m.data are the mag_squared of the fft output
        # m.raw_data is a string that contains the binary floats.
        # You could write this as binary to a file.

        # Scanning rate
        if timestamp == 0:
            timestamp = time.time()
            centerfreq = m.center_freq
        if m.center_freq < centerfreq:
            print "HI"
            sys.stderr.write("scanned %.1fMHz in %.1fs\n" % ((centerfreq - m.center_freq)/1.0e6, time.time() - timestamp))
            timestamp = time.time()
            print "Mean Power = " , sump/counter
            if (sump/counter)>5.5:
                print "Signal Detected!"
                res = True
                break
            else:
                break
        centerfreq = m.center_freq
        prev_db = 0
        counter = 1
        sump = 0
        for i_bin in range(bin_start, bin_stop):

            center_freq = m.center_freq
            freq = bin_freq(i_bin, center_freq)
                #noise_floor_db = -174 + 10*math.log10(tb.channel_bandwidth)
            noise_floor_db = 10*math.log10(min(m.data)/tb.usrp_rate)
            power_db = 10*math.log10(m.data[i_bin]/tb.usrp_rate) - noise_floor_db
            sump = sump + power_db
            counter = counter + 1
                #if (power_db > tb.squelch_threshold) and (freq >= tb.min_freq) and (freq <= tb.max_freq):
                    #print datetime.now(), "center_freq", center_freq, "freq", freq, "power_db", power_db, "noise_floor_db", noise_floor_db
    return res
