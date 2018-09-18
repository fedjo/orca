import pmt

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
        self.freq = self.ch_list[ch_index]

    def handler(self, pdu):
        self.message_port_pub(pmt.intern('sync'), pmt.cons(pmt.intern("freq"), pmt.to_pmt(self.freq)))
        self.ch_index = (self.ch_index + 1) % ch_len
        self.freq = self.ch_list[self.ch_index]

