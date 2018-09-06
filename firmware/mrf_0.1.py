import os
import sys
from argparse import ArgumentParser
from gnuradio import gr


from sense.spectrum_sense import sense, sense_path
from comm.tx import tx_path
from comm.rx import rx_path


class infrastructure(gr.top_block):
    def __init__(self, channel_bandwidth, min_freq, max_freq, s_samp_rate,
                 tune_delay, dwell_delay, s_gain, c_samp_rate, c_gain, freq, code1, code2):
        gr.top_block.__init__(self)


        sensepath = sense_path(channel_bandwidth, min_freq, max_freq, s_samp_rate,
                                tune_delay, dwell_delay, s_gain)
        txpath = tx_path(c_samp_rate, c_gain, freq, code1, code2)
        rxpath = rx_path(c_samp_rate, c_gain, freq, code1, code2)

        self.connect(sense_path)
        self.connect(tx_path)
        self.connect(rx_path)


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

    channels = [ [499100000,500100000], [599100000,600100000] ]
    code1 = '010110011011101100010101011111101001001110001011010001101010001'
    code2 = '11011010110111011000110011110101100010010011110111'
    a = [1]*len(channels)

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


    min_freq = 0
    max_freq = 5
    infra = infrastructure(args.channel_bandwidth, min_freq, max_freq, args.s_samp_rate,
        args.tune_delay, args.dwell_delay, args.s_gain, args.c_samp_rate, args.c_gain,
        args.freq, code1, code2)
    infra.strart()



    for i in range(0, len(channels)):
        start_freq = channels[i][0]
        finish_freq = channels[i][1]
        rate = 500000
        gain = 80
        sp = sense_path(6.25e3, start, finish, rate, 0.25, 0.25,gain)
        try:
            sp.start()
            if(sense(sp)):
                a[i] = 0
            print(a[i])
        except KeyboardInterrupt:
            pass
        finally:
            sp.stop()
