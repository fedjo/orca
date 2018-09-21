import os
import sys
import time
import pmt
import threading
import ConfigParser
from argparse import ArgumentParser

import scipy
from gnuradio import gr
from gnuradio import uhd
from gnuradio import blocks

from sense.spectrum_sense import spectrum_sense
from sense.pu import detect_pu
from comm.tx import tx_path
from comm.rx import rx_path
from utils import utils
from utils import ublocks


class FreqSweeper(threading.Thread):
    def __init__(self, chlist, usrp):
        Thread.__init__(self)
        self.chlist = chlist
        self.chidx = 0
        self.usrp = usrp



    def run(self):
        while 1:
            self.usrp.set_center_freq(self.chlist[self.chidx], 0)
            time.sleep(0.3)
            print("USRP listening in: {}".format(self.usrp.get_center_freq()))
            self.chidx = (self.chidx + 1) % len(self.chlist)


class infrastructure(gr.top_block):
    def __init__(self, samp_rate, freq, bandwidth, code1, code2):
        gr.top_block.__init__(self, "Infrastructure")

	    ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate
        self.freq = freq
        self.bandwidth = bandwidth
        self.code1 = code1
        self.code2 = code2

        ##################################################
        # Blocks
        ##################################################

        self.u = uhd.usrp_source(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.u.set_samp_rate(samp_rate)
        self.u.set_center_freq(freq, 0)
        self.u.set_gain(60, 0)
        self.u.set_bandwidth(bandwidth, 0)

        self.message_strobe = blocks.message_strobe(pmt.cons(pmt.intern("freq"),
                                                    pmt.to_pmt(600e6)), 2000)

        self.sweeper = ublocks.frequency_sweeper()
        self.tag_print = ublocks.sample_separator()
        self.tag_print2 = ublocks.sample_separator()
        self.sensepath = spectrum_sense()
        self.detect_pu = detect_pu(code1)
        #txpath = tx_path(samp_rate, freq, code2)
        #self.rxpath = rx_path(samp_rate, freq, code1)

        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.message_strobe, 'strobe'), (self.sweeper, 'clock'))
        self.msg_connect((self.sweeper, 'sync'), (self.u, 'command'))
        #self.connect(self.u, self.tag_print2)
        #self.connect(self.tag_print2, self.detect_pu)
        #self.connect(self.u, self.tag_print)
        #self.connect(self.tag_print, self.sensepath)
        self.connect(self.u, self.detect_pu)
        self.connect(self.u, self.sensepath)


    def get_sensepath_sink_queue(self):
        if self.sensepath:
            return self.sensepath.sense_sink_queue

    def get_detectpu_sink_queue(self):
        if self.detect_pu:
            return self.detect_pu.pu_sink_queue

    def get_ss(self):
        return self.sensepath

    def set_ss(self, sensepath):
        self.sensepath = sensepath

    def get_tx(self):
        return self.txpath

    def set_tx(self, txpath):
        self.txpath = txpath

    def get_rx(self):
        return self.rxpath

    def set_rx(self, rxpath):
        self.rxpath = rxpath


def args_parse():
    parser = ArgumentParser(description="Software Defined Radio firmware based on MRF")

    # FIXME
    # Missing setting min_freq/max_freq
    # Probably this should be read from a conf file as whole parameters
    general_args = parser.add_argument_group('General Arguments', '')
    general_args.add_argument("-c", "--config", type=str, default="config.ini",
                            help="Specify the configuration file [default=%(default)s]")
    general_args.add_argument("-a", "--args", type=str, default="",
                            help="UHD device device address args [default=%(default)s]")
    general_args.add_argument("-s", "--spec", type=str, default=None,
                            help="Subdevice of UHD device where appropriate")
    general_args.add_argument("-A", "--antenna", type=str, default=None,
                            help="Select Rx Antenna where appropriate")
    general_args.add_argument("-f", "--freq", type=float, default=None,
                            help="Set frequency to communicate")
    general_args.add_argument("-sr", "--samp-rate", type=float, default=64e3,
                            help="Set sample rate [default=%(default)s]")
    general_args.add_argument("-b", "--channel-bandwidth", type=float, default=6.25e3, metavar="Hz",
                            help="Channel bandwidth of fft bins in Hz [default=%(default)s]")
    general_args.add_argument("-td", "--tune-delay", type=float, default=0.25, metavar="SECS",
                            help="Time to delay (in seconds) after changing frequency [default=%(default)s]")
    general_args.add_argument("-dd", "--dwell-delay", type=float, default=0.25, metavar="SECS",
                            help="Time to dwell (in seconds) at a given frequency [default=%(default)s]")
    general_args.add_argument("-rt", "--real-time", action="store_true", default=False,
                            help="Attempt to enable real-time scheduling")
    sense_args = parser.add_argument_group('Sensing Arguments', 'Set the Spectrum Sensing Path')
    sense_args.add_argument("-sg", "--s-gain", type=float, default=None,
                            help="Set gain in dB (default is midpoint)")

    comm_args = parser.add_argument_group('Communication Arguments', 'Set the Receive/Transmit Path')
    comm_args.add_argument("-cg", "--c-gain", type=float, default=None,
                            help="Set gain in dB (default is midpoint)")

    # (options, args) = parser.parse_args()
    return parser.parse_args()


if __name__ == '__main__':

    args = args_parse()

    if not args.real_time:
        realtime = False
    else:
        # Attempt to enable realtime scheduling
        r = gr.enable_realtime_scheduling()
        if r == gr.RT_OK:
            realtime = True
        else:
            realtime = False
            print "Note: failed to enable realtime scheduling"

    if not args.config:
        args.config = "config.ini"

    config =  ConfigParser.ConfigParser()
    config.read(args.config)
    general = lambda p: config.get('GENERAL', p)
    sensing = lambda p: config.get('SENSING', p)
    comm = lambda p: config.get('COMMUNICATION', p)

    infra = infrastructure(int(general('samp_rate')), float(general('freq')), float(general('bandwidth')), comm('code1'), comm('code2'))

    # Get message queue of detect_pu
    detect_pu_q = infra.get_detectpu_sink_queue()
    # Get message queue of sensing
    sense_q = infra.get_sensepath_sink_queue()

    # Channel to use
    channel_list = [600e6, 825e6, 1.2e9, 2.4e9]
    print("The specified channels are: {}".format(channel_list))

    # Control channels for busy tones
    busy_tone_channels = [520e6,540e6,560e6,580e6]

    # Energy threshold for each channel
    thresholds = [-16,-18,-19,-30]

    # Node u vector
    u = [0]*len(channel_list)
    print("U = {}".format(u))

    # u vectors of the other nodes
    u_vectors = [ [0]*len(channel_list) ] * (int(general('nodes_no'))-1)
    print("U vector of others = {}".format(u_vectors))

    # Calculate a = []
    # Node a vector
    a = [0]*len(channel_list)
    print("A = {}".format(a))

    infra.start()

    while 1:
        # Detection of Primary Users
        #detect_pu_q.flush()
        #sense_q.flush()
        #infra.detect_pu.uhd_usrp_source_0.set_center_freq(ch, 0)
        usrp_freq = infra.u.get_center_freq()
        print("USRP in freq: {}".format(usrp_freq))
        i = utils.get_ch_index(usrp_freq)

        # Scan for PUs

        # Message Sink
        if detect_pu_q.count():
            print("PU Queue in channel: {} has total of: {} items".format(usrp_freq, detect_pu_q.count()))
            val = detect_pu_q.delete_head().to_string()
            if val:
                a[i] = 1
            detect_pu_q.flush()

        # Probe Signal
        my_pudata = infra.detect_pu.blocks_probe_signal_0.level()
        print("PU DETECT data from probe signal: {}".format(my_pudata))

        # Probe signal Vector
        my_vpudata = infra.detect_pu.blocks_probe_signal_vector_0.level()
        print("Sense Data from probe signal vector: {}".format(my_vpudata))



        print("Print availability vector: a = {}".format(a))

        # Sensing & Collision detection
        # Scan energy for collision detection

        # Message Sink
        if (sense_q.count() and a[i] == 0):
            print("Sense Queue in channel: {} has total of: {} items".format(usrp_freq, sense_q.count()))
            val2 = sense_q.delete_head().to_string()
            db_vector = scipy.fromstring(val2, dtype=scipy.float32)
            print("Queue  has {}".format(db_vector))
            mean_db = utils.calc_mean_energy(db_vector)
            print("Mean db {}".format(mean_db))
            with open('data.out', 'aw+') as f:
                f.write('\t\t\t\t'*i + '{}'.format(mean_db) + '\n')
            channel_state = utils.detect_collision(mean_db, channel_list[i], thresholds[i], busy_tone_channels[i])
            if (channel_state==2):
                print("Busy Tone")
                #transmissions.transmit_busy_tone(busy_tone_channels[i], bandwidth)
                pass
            sense_q.flush()

        # Probe signal
        my_data = infra.sensepath.blocks_probe_signal_0.level()
        print("Sense Data from probe signal: {}".format(my_data))

        # Probe signal Vector
        my_vdata = infra.sensepath.blocks_probe_signal_vector_0.level()
        print("Sense Data from probe signal vector: {}".format(my_vdata))


        # TODO
        # Calculate n = [] from U vectors previously received
        n = utils.calc_vectorN(u_vectors)
        print("N = {}".format(n))

       # send busy tones
       # for i in range(0, channel_list):

        # evaluation of cost function
        penalty = -5
        prize = 5
        #c = utils.cost(u_vector, busy_tone_channels, penalty, prize)

        #time.sleep(0.2)
