import os
import sys
import ConfigParser
from argparse import ArgumentParser

from gnuradio import gr

from sense.spectrum_sense import spectrum_sense
from comm.tx import tx_path
from comm.rx import rx_path


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
        #txpath = tx_path(samp_rate, freq, code2)
        self.rxpath = rx_path(samp_rate, freq, code1)

        self.connect(self.sensepath)

    def get_msg_sink_queue(self):
        if self.sensepath:
            return self.sensepath.sink_queue

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


def find_average(vector):
    avg = []
	n = int(len(vector)/1024)

	for i in range(0, n):
		avg.append(sum(vector[i*1024:i*1024+1024])/1024)

	#print avg
	return sum(avg)/len(avg)


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

    infra = infrastructure(int(comm('c_samp_rate')), float(general('freq')), float(general('bandwidth')), comm('code1'), comm('code2'))

    infra.start()
    sense_queue = infra.get_msg_sink_queue()
    try:
        while 1:
            if sense_queue.count:
            pkt = sense_queue.delete_head().to_string()
            v = scipy.fromstring(pkt, dtype=scipy.float32)
            print(v)
            print(find_average(v))

        raw_input("Press Enter to quit")
    except EOFError:
        pass
    infra.stop()
    infra.wait()
