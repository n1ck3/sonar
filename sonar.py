#!/usr/bin/env python3

"""
sonar.

Usage:
    sonar.py search (artists|albums|songs) SEARCH_STRING... [--limit LIMIT]
    sonar.py random (albums|songs) [--limit LIMIT]
    sonar.py shell

    sonar.py (-h | --help)
    sonar.py (-v | --verbose)
    sonar.py --version

Options:
    -n LIMIT, --limit LIMIT     Limit results [default: 10]
    -h --help                   Shows this screen
    -v --verbose                Verbose output (i.e. debug)
    --version                   Show version

"""

__author__ = "Niclas Helbro <niclas.helbro@gmail.com>"
__version__ = "Sonar 0.1.0"

from docopt import docopt

from sonar.client import Client
from sonar.player import Player

import libsonic

import os
import sys
import configparser

# def pretty(data, indent=2):
#     print(
#         json.dumps(
#             (data),
#             sort_keys=True,
#             indent=indent
#         )
#     )

# def debug(data):
#     print("[debug] %s" % data)

# def exit(self, state):
#     # Stop players and threads and whatnot
#     sys.exit(state)

def connect():
    config_file = "%s/.sonar.conf" % os.path.expanduser('~')

    # Check for .sonar.conf in users home dir.
    if not os.path.exists(config_file):
        config_file = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-1]), ".sonar.conf")

        # Check for .sonar.conf in the directory of sonar.py
        if not os.path.exists(config_file):
            print("No config file found.\n")
            print("Copy and modify `sonar.conf` to either \n`~/.sonar.conf` or `/path/to/sonar/.sonar.conf`\n")
            sys.exit(0)

    config = configparser.ConfigParser()
    config.read(config_file)

    return libsonic.Connection(
        config["server"]["host"],
        config["server"]["user"],
        config["server"]["password"],
        port=config["server"]["port"]
    )

if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

    conn = connect()
    client = Client(conn)
    player = Player(conn)

    if "search" in args and args["search"]:
        client.get_search(args)
    elif "random" in args and args["random"]:
        client.get_random(args)
    elif "shell" in args and args["shell"]:
        client.shell()

    # debug(args)
