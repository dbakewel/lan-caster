"""startserver module.

Parses command line arguments, loads server module,
creates Server instance, and call run() on Server.
"""

import argparse
import os
import engine.time as time

from engine.log import log
from engine.log import setLogLevel

# only import msgpack here to make sure it is installed.
try:
    import msgpack
except BaseException:
    log("Python package missing. Install with something similar to:\n py -3 -m pip install msgpack", "FAILURE")
    exit()

import engine.network
import engine.loaders


def startServer():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-game', metavar='dir', dest='game', type=str,
                        default='demo', help="Directory to load game from")

    parser.add_argument('-register', metavar='name', dest='registerName', type=str,
                        default=False, help='Experimental: Register with connector as name (False == do not register)')
    parser.add_argument('-ch', metavar='hostname', dest='connectorHostName', type=str,
                        default='lan-caster.net', help='Experimental: Connector hostname or IP address')
    parser.add_argument('-cp', metavar='port', dest='connectorPort', type=int,
                        default=20000, help='Experimental: Connector port number')

    parser.add_argument('-sip', metavar='ipaddr', dest='serverIP', type=engine.network.argParseCheckIPFormat,
                        default='0.0.0.0', help='Server IP address')
    parser.add_argument('-sp', metavar='port', dest='serverPort', type=int,
                        default=20001, help='Server port number')

    parser.add_argument('-fps', metavar='fps', dest='fps', type=int,
                        default=30, help='Target frames per second (aka steps/sec)')
    parser.add_argument('-busy', metavar='secs', dest='busySec', type=int,
                        default=60, help='Seconds between logging percent busy')
    parser.add_argument('-pause', metavar='secs', dest='pause', type=int,
                        default=0, help='Duration to pause in seconds before starting server (for testing)')
    parser.add_argument('-test', dest='testMode', action='store_true',
                        default=False, help='Start server in test mode')

    parser.add_argument('-profile', dest='profile', action='store_true',
                        default=False, help='Print function performance profile on exit.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages (includes -verbose)')

    args = parser.parse_args()

    setLogLevel(args.debug, args.verbose)

    if(args.pause):
        log(f"Pausing for {args.pause} seconds before starting server.")
        time.sleep(sec=args.pause)

    module = engine.loaders.loadModule("server", game=args.game)
    module.Server(args).run()


if __name__ == "__main__":
    startServer()
