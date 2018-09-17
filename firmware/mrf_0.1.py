import os
import sys
import ConfigParser
from argparse import ArgumentParser

import scipy
from gnuradio import gr

from sense.spectrum_sense import spectrum_sense
from sense.pu import detect_pu
from comm.tx import tx_path
from comm.rx import rx_path
from utils import utils


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

        self.sensepath = spectrum_sense(samp_rate, freq, bandwidth)
        self.detect_pu = detect_pu(freq, bandwidth, samp_rate, code1)
        #txpath = tx_path(samp_rate, freq, code2)
        self.rxpath = rx_path(samp_rate, freq, code1)


    def start_detect_pu(self):
        self.connect(self.detect_pu)
        gr.top_block.start(self)

    def start_sense(self):
        self.connect(self.sensepath)
        gr.top_block.start(self)

    def get_sensepath_sink_queue(self):
        if self.sensepath:
            return self.sensepath.sink_queue

    def get_detectpu_sink_queue(self):
        if self.detect_pu:
            return self.detect_pu.sink_queue

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

    sense_queue = infra.get_sensepath_sink_queue()
    detect_pu_queue = infra.get_detectpu_sink_queue()

    channel_list = [600e6, 825e6, 1.2e9, 2.4e9]
    print("The specified channels are: {}".format(channel_list))
    busy_tone_channels = [520e6,540e6,560e6,580e6]
    thresholds = [-16,-18,-19,-30]

    u = [0]*len(channel_list)
    u_vectors = [ [0]*len(channel_list) ] * (int(general('nodes_no'))-1)
    print("U = {}".format(u))
    print("U vector of others = {}".format(u_vectors))

    # Calculate a = []
    a = [0]*len(channel_list)
    print("A = {}".format(a))
    i = 0

    while 1:
        # Detection of Primary Users
        infra.start_detect_pu()
        for ch in channel_list:
            infra.detect_pu.uhd_usrp_source_0.set_center_freq(ch, 0)
            # Scan for PUs
            if detect_pu_queue.count():
                val = detect_pu_queue.delete_head().to_string()
                av = scipy.fromstring(val, dtype=scipy.float32)
                print(av)
                a[i] = av
            i += 1
        infra.disconnect_all()
        infra.stop()
        infra.wait()
        print("Print availability vector: a = {}".format(a))

        # Sensing & Collision detection
        i = 0
        infra.start_sense()
        for ch in channel_list:
            # Scan energy for collision detection
            if sense_queue.count():
                val2 = sense_queue.delete_head().to_string()
                db_vector = scipy.fromstring(val, dtype=scipy.float32)
                mean_db = calc_mean_energy(db_vector)
                channel_state = utils.detect_collision(mean_db, channel_list[i], threshold[i], busy_tone_channels[i])
                if (channel_state==2):
                    print("Busy Tone")
                    #transmissions.transmit_busy_tone(busy_tone_channels[i], bandwidth)
                    pass
            i += 1
        infra.disconnect_all()
        infra.stop()
        infra.wait()




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
