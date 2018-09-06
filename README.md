# Project Title

Software Defined Radio firmware based on a Markov Random Field framework

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

On a GNU/Linux Debian Stretch machine install

* python 2.7
* gnuradio

```
sudo apt-get update
sudo apt-get dist-upgrade
sudo apt-get install python gnuradio
```

### Installing

Clone git repository on your machine.
On a console run:

```
git clone https://github.com/fedjo/orca.git
```

Move into directory 'firmware' and run
the firmware

```
cd firmware
python mrf_0.1.py -h
```

You should get the following output


```
usage: mrf_0.1.py [-h] [-a ARGS] [-s SPEC] [-A ANTENNA] [-sr S_SAMP_RATE]
                  [-sg S_GAIN] [-td SECS] [-dd SECS] [-b Hz] [-l Hz] [-q dB]
                  [-F FFT_SIZE] [-rt] [-cr C_SAMP_RATE] [-cg C_GAIN] [-f FREQ]

Software Defined Radio firmware based on MRF

optional arguments:
  -h, --help            show this help message and exit

Sensing Arguments:
  Set the Spectrum Sensing Path

  -a ARGS, --args ARGS  UHD device device address args [default=]
  -s SPEC, --spec SPEC  Subdevice of UHD device where appropriate
  -A ANTENNA, --antenna ANTENNA
                        Select Rx Antenna where appropriate
  -sr S_SAMP_RATE, --s-samp-rate S_SAMP_RATE
                        Set sensing sample rate [default=1000000.0]
  -sg S_GAIN, --s-gain S_GAIN
                        Set gain in dB (default is midpoint)
  -td SECS, --tune-delay SECS
                        Time to delay (in seconds) after changing frequency
                        [default=0.25]
  -dd SECS, --dwell-delay SECS
                        Time to dwell (in seconds) at a given frequency
                        [default=0.25]
  -b Hz, --channel-bandwidth Hz
                        Channel bandwidth of fft bins in Hz [default=6250.0]
  -l Hz, --lo-offset Hz
                        lo_offset in Hz [default=0]
  -q dB, --squelch-threshold dB
                        Squelch threshold in dB [default=None]
  -F FFT_SIZE, --fft-size FFT_SIZE
                        Specify number of FFT bins
                        [default=samp_rate/channel_bw]
  -rt, --real-time      Attempt to enable real-time scheduling

Communication Arguments:
  Set the Receive/Transmit Path

  -cr C_SAMP_RATE, --c-samp-rate C_SAMP_RATE
                        Set sensing sample rate [default=1000000.0]
  -cg C_GAIN, --c-gain C_GAIN
                        Set gain in dB (default is midpoint)
  -f FREQ, --freq FREQ  Set frequency to communicate

```

## Running the tests


## Built With

* [Python 2.7](https://www.python.org/download/releases/2.7/) - The language used
* [Gnuradio 3.7.10.1-2](https://www.gnuradio.org/) - The SDR software used

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/fedjo/orca/tags).

## Related works:

 * [A Markov Random Field framework for channel assignment in Cognitive Radio networks](https://ieeexplore.ieee.org/document/6197617/)

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
