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
import libsonic

import os
import sys
import re
import json
import shlex
import configparser


class Client(object):
    def __init__(self):
        config_file = "%s/.sonar.conf" % os.path.expanduser('~')

        # Check for .sonar.conf in users home dir.
        if not os.path.exists(config_file):
            config_file = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-1]), ".sonar.conf")

            # Check for .sonar.conf in the directory of sonar.py
            if not os.path.exists(config_file):
                print("No config file found.\n")
                print("Copy and modify `sonar.conf` to either \n`~/.sonar.conf` or `/path/to/sonar/.sonar.conf`\n")
                sys.exit(0)

        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.conn = libsonic.Connection(
            self.config["server"]["host"],
            self.config["server"]["user"],
            self.config["server"]["password"],
            port=self.config["server"]["port"]
        )

        self._current_list = None

    def _print_artists(self, artists):
        if type(artists) == dict:
            artists = [artists]

        idx = 0
        for artist in artists:
            _print("%s: %s" % (
                idx,
                artist['name']
            ))
            idx += 1

    def _print_albums(self, albums):
        if type(albums) == dict:
            albums = [albums]

        idx = 0
        for album in albums:
            _print("%s: %s (%s)" % (
                idx,
                album['album'],
                album['artist']
            ))
            idx += 1

    def _print_songs(self, songs):
        if type(songs) == dict:
            songs = [songs]

        idx = 0
        for song in songs:
            _print("%s: %s (%s)" % (
                idx,
                song['title'],
                song['artist']
            ))
            idx += 1

    def exit(self, state):
        # Stop players and threads and whatnot
        sys.exit(state)

    def get_random(self, args):
        if "albums" in args and args["albums"]:
            res = self.conn.getAlbumList(ltype="random", size=args['--limit'])
            self._print_albums(res['albumList']['album'])
        elif "songs" in args and args["songs"]:
            res = self.conn.getRandomSongs(size=args["--limit"])
            self._print_songs(res['randomSongs']['song'])

    def get_search(self, args):
        query = " ".join(args["SEARCH_STRING"])
        kwargs = {
            "artistCount": 0,
            "artistOffset": 0,
            "albumCount": 0,
            "albumOffset": 0,
            "songCount": 0,
            "songOffset": 0
        }
        if "artists" in args and args["artists"]:
            kwargs["artistCount"] = args['--limit']
            res = self.conn.search2(query, **kwargs)
            if "artist" in res["searchResult2"]:
                self._print_artists(res["searchResult2"]["artist"])
            else:
                print("Nothing found...")
        elif "albums" in args and args["albums"]:
            kwargs["albumCount"] = args['--limit']
            res = self.conn.search2(query, **kwargs)
            if "album" in res["searchResult2"]:
                self._print_albums(res["searchResult2"]["album"])
            else:
                print("Nothing found...")
        elif "songs" in args and args["songs"]:
            kwargs["songCount"] = args['--limit']
            res = self.conn.search2(query, **kwargs)
            if "song" in res["searchResult2"]:
                self._print_songs(res['searchResult2']['song'])
            else:
                print("Nothing found...")


    def shell(self):
        """
        Interactive shell, yeah.

        """
        welcome = "Welcome to %s.\n" % __version__
        welcome += "Written by %s\n" % __author__
        print(welcome)

        while True:
            try:
                raw = input(">>> ")
            except EOFError as e:
                print("\nExiting")
                self.exit(0)
            except KeyboardInterrupt as e:
                print("\nInterrupted: Exhting")
                self.exit(0)

            try:
                args = docopt(__doc__, argv=shlex.split(raw), version=__version__)
            except:
                print("Malformed input")

def pretty(data, indent=2):
    print(
        json.dumps(
            (data),
            sort_keys=True,
            indent=indent
        )
    )

def debug(data):
    print("[debug] %s" % data)


def _print(data):
    if type(data) == str:
        data = data.replace(r'&#228;', r'ä')
        data = data.replace(r'&#229;', r'å')
        data = data.replace(r'&#233;', r'é')
        data = data.replace(r'&#246;', r'ö')

    print(data)


if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

    client = Client()

    if "search" in args and args["search"]:
        # debug("SEARCH")
        client.get_search(args)
    elif "random" in args and args["random"]:
        # debug("RANDOM")
        client.get_random(args)
    elif "shell" in args and args["shell"]:
        # debug("SHELL")
        client.shell()

    # debug(args)
