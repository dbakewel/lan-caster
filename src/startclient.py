"""startclient module.

Parses command line arguments, loads client module,
creates Client instance, and call run() on Client.
"""

import argparse
import os
import engine.time as time

from engine.log import log
from engine.log import setLogLevel

# only import msgpack and pygame here to make sure they are installed.
try:
    import pygame
    import msgpack
except BaseException:
    log("Python packages missing. Install with something similar to:\n py -3 -m pip install pygame msgpack", "FAILURE")
    exit()

import engine.network
import engine.loaders


def startClient():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-game', metavar='dir', dest='game', type=str,
                        default='demo', help="Directory to load game from")
    parser.add_argument('-player', metavar='name', dest='playerDisplayName', type=str,
                        default='anonymous', help="Player's name to display in game")

    parser.add_argument('-connect', metavar='name', dest='connectName', type=str,
                        default=False, help='Experimental: Connect to server using connector. "name" must match server\'s "-register name" (if False then use -sip and -sp to connect to server)')
    parser.add_argument('-ch', metavar='hostname', dest='connectorHostName', type=str,
                        default='lan-caster.net', help='Experimental: Connector hostname or IP address')
    parser.add_argument('-cp', metavar='port', dest='connectorPort', type=int,
                        default=20000, help='Experimental: Connector port number')

    parser.add_argument('-sip', metavar='ipaddr', dest='serverIP', type=engine.network.argParseCheckIPFormat,
                        default='127.0.0.1', help='Server IP address')
    parser.add_argument('-sp', metavar='port', dest='serverPort', type=int,
                        default=20001, help='Server port number')

    parser.add_argument('-ip', metavar='ipaddr', dest='clientIP', type=str,
                        default='0.0.0.0', help='Client IP address')
    parser.add_argument('-p', metavar='port', dest='clientPort', type=int,
                        default=20002, help='Client port number (client will search for an available port starting with this number.)')

    parser.add_argument('-width', metavar='width', dest='windowWidth', type=int,
                        default=640, help='Window width')
    parser.add_argument('-height', metavar='height', dest='windowHeight', type=int,
                        default=640, help='Window height')
    parser.add_argument('-fps', metavar='fps', dest='fps', type=int,
                        default=30, help='Target frames per second')
    parser.add_argument('-busy', metavar='secs', dest='busySec', type=int,
                        default=60, help='Seconds between logging percent busy')
    parser.add_argument('-pause', metavar='secs', dest='pause', type=int,
                        default=0, help='Duration to pause in seconds before starting client (for testing)')

    parser.add_argument('-profile', dest='profile', action='store_true',
                        default=False, help='Print function performance profile on exit.')
    parser.add_argument('-verbose', dest='verbose', action='store_true',
                        default=False, help='Print VERBOSE level log messages')
    parser.add_argument('-debug', dest='debug', action='store_true',
                        default=False, help='Print DEBUG level log messages (includes -verbose)')

    args = parser.parse_args()

    setLogLevel(args.debug, args.verbose)

    if(args.pause):
        log(f"Pausing for {args.pause} seconds before starting client.")
        time.sleep(sec=args.pause)

    module = engine.loaders.loadModule("client", game=args.game)
    module.Client(args).run()


if __name__ == '__main__':
    startClient()
