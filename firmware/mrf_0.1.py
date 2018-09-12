import os
import sys
import ConfigParser
from argparse import ArgumentParser

from gnuradio import gr

from sense.channel_energy import orig_single_channel
from comm.tx import tx_path
from comm.rx import rx_path


class infrastructure(gr.top_block):
    # def __init__(self, channel_bandwidth, min_freq, max_freq, s_samp_rate,
    #              tune_delay, dwell_delay, s_gain, c_samp_rate, c_gain, freq, code1, code2):
    def __init__(self):
        gr.top_block.__init__(self)
        self.ss = None
        self.tx = None
        self.rx = None


    def get_msg_sink_queue(self):
        if self.ss:
            return self.ss.sink_queue

    def get_ss(self):
        return self.ss

    def set_ss(self, ss):
        self.ss = ss

    def get_tx(self):
        return self.tx

    def set_tx(self, tx):
        self.tx = tx

    def get_rx(self):
        return self.rx

    def set_rx(self, rx):
        self.rx = rx


def args_parse():
    parser = ArgumentParser(description="Software Defined Radio firmware based on MRF")

    # FIXME
    # Missing setting min_freq/max_freq
    # Probably this should be read from a conf file as whole parameters
    sense_args = parser.add_argument_group('Sensing Arguments', 'Set the Spectrum Sensing Path')
    sense_args.add_argument("-a", "--args", type=str, default="",
                            help="UHD device device address args [default=%(default)s]")
    sense_args.add_argument("-s", "--spec", type=str, default=None,
                            help="Subdevice of UHD device where appropriate")
    sense_args.add_argument("-A", "--antenna", type=str, default=None,
                            help="Select Rx Antenna where appropriate")
    sense_args.add_argument("-sr", "--s-samp-rate", type=float, default=1e6,
                            help="Set sensing sample rate [default=%(default)s]")
    sense_args.add_argument("-sg", "--s-gain", type=float, default=None,
                            help="Set gain in dB (default is midpoint)")
    sense_args.add_argument("-td", "--tune-delay", type=float, default=0.25, metavar="SECS",
                            help="Time to delay (in seconds) after changing frequency [default=%(default)s]")
    sense_args.add_argument("-dd", "--dwell-delay", type=float, default=0.25, metavar="SECS",
                            help="Time to dwell (in seconds) at a given frequency [default=%(default)s]")
    sense_args.add_argument("-b", "--channel-bandwidth", type=float, default=6.25e3, metavar="Hz",
                            help="Channel bandwidth of fft bins in Hz [default=%(default)s]")
    sense_args.add_argument("-l", "--lo-offset", type=float, default=0, metavar="Hz",
                            help="lo_offset in Hz [default=%(default)s]")
    sense_args.add_argument("-q", "--squelch-threshold", type=float, default=None, metavar="dB",
                            help="Squelch threshold in dB [default=%(default)s]")
    sense_args.add_argument("-F", "--fft-size", type=int, default=None,
                            help="Specify number of FFT bins [default=samp_rate/channel_bw]")
    sense_args.add_argument("-rt", "--real-time", action="store_true", default=False,
                            help="Attempt to enable real-time scheduling")

    comm_args = parser.add_argument_group('Communication Arguments', 'Set the Receive/Transmit Path')
    comm_args.add_argument("-cr", "--c-samp-rate", type=float, default=1e6,
                            help="Set sensing sample rate [default=%(default)s]")
    comm_args.add_argument("-cg", "--c-gain", type=float, default=None,
                            help="Set gain in dB (default is midpoint)")
    comm_args.add_argument("-f", "--freq", type=float, default=None,
                            help="Set frequency to communicate")

    # (options, args) = parser.parse_args()
    return parser.parse_args()


if __name__ == '__main__':

    # args = args_parse()

    # if not args.real_time:
    #     realtime = False
    # else:
    #    # Attempt to enable realtime scheduling
    #    r = gr.enable_realtime_scheduling()
    #    if r == gr.RT_OK:
    #        realtime = True
    #    else:
    #        realtime = False
    #        print "Note: failed to enable realtime scheduling"

    config =  ConfigParser.ConfigParser()
    config.read('config.ini')
    general = lambda p: config.get('GENERAL', p)
    sensing = lambda p: config.get('SENSING', p)
    comm = lambda p: config.get('COMMUNICATION', p)

    infra = infrastructure()

    while 1:
        _a = input("Please choose which functionality to excecute\n"
                   "sensing/transmit/receive/quit)\n s/t/r/q?")

        if _a == 's':
            #sensepath = sense_path(float(sensing('channel_bandwidth')), float(min_freq), float(max_freq),
            #                       int(sensing('s_samp_rate')), float(sensing('tune_delay')),
            #                       float(sensing('dwell_delay')), int(sensing('s_gain')))
            sensepath = orig_single_channel(float(general('freq')), float(general('bandwidth')))
            # infra.connect(sense_path)
            infra.set_ss(sensepath)
            infra.start()
            sense_queue = infra.get_msg_sink_queue()
            while 1:
                if sense_queue.count():
                    pkt = sense_queue.delete_head().to_string()
                    print("Number of items in queue: {}".format(sense_queue.count()))
                    print("Found value: {}".format(pkt))
                    _s = raw_input("Press q to break")
                    if _s == 'q':
                        break
        elif _a == 't':
            txpath = tx_path(int(comm('c_samp_rate')), int(comm('c_gain')), float(comm('freq')), comm('code1'), comm('code2'))
            # infra.connect(tx_path)
            infra.set_tx(txpath)
        elif _a == 'r':
            rxpath = rx_path(int(comm('c_samp_rate')), int(comm('c_gain')), float(comm('freq')), comm('code1'), comm('code2'))
            # infra.connect(rx_path)
            infra.set_rx(rxpath)
        elif _a == 'q':
            infra.stop()
        else:
            break
            continue
