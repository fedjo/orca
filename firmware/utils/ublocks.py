import pmt

import numpy
from gnuradio import gr

class frequency_sweeper(gr.sync_block):
    def __init__(self, channel_list=[600e6, 825e6, 1.2e9, 2.4e9]):  # only default arguments here
        gr.sync_block.__init__(
            self,
            name='Frequency sweeper',
            in_sig=[],
            out_sig=[]
        )
        self.message_port_register_in(pmt.intern('clock'))
        self.set_msg_handler(pmt.intern('clock'), self.handler)
        self.message_port_register_out(pmt.intern('sync'))
        self.ch_list = channel_list
        self.ch_len = len(channel_list)
        self.ch_index = 0
        self.freq = self.ch_list[self.ch_index]

    def handler(self, pdu):
        self.message_port_pub(pmt.intern('sync'), pmt.cons(pmt.intern("freq"), pmt.to_pmt(self.freq)))
        self.ch_index = (self.ch_index + 1) % self.ch_len
        self.freq = self.ch_list[self.ch_index]


class sample_separator(gr.sync_block):
    def __init__(self):  # only default arguments here
        gr.sync_block.__init__(
            self,
            name='Sample Separator',
            in_sig=[numpy.float32],
            out_sig=[numpy.float32]
        )

        def work(self, input_items, output_items):
            in0 = input_items[0]
            out = output_items[0]
            # Get and print tags found on input_stream
            tags = get_tags_in_window(input_items[0], 0, len(input_items[0]))
            print("Tags found on USRP output_stream: {}".format(tags))
            #
            out[:] = in0
            return len(output_items[0])

