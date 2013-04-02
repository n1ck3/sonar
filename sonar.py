#!/usr/bin/env python3

"""
sonar.

Usage:
    sonar.py search [(artist|album|song) SEARCH_STRING...] [--limit LIMIT]
    sonar.py random [album|song] [--limit LIMIT]
    sonar.py last
    sonar.py play [INDEX]
    sonar.py pause
    sonar.py (playpause|pp)
    sonar.py stop
    sonar.py (prev|next)
    sonar.py (rw|ff) [TIMEDELTA]
    sonar.py queue [show|clear|[[set|prepend|append] INDEX...]]
    sonar.py status [--short]
    sonar.py

    sonar.py (-h | --help)
    sonar.py (-v | --verbose)
    sonar.py --version

Options:
    -n LIMIT, --limit LIMIT     Limit results [default: 10]
    -h --help                   Shows this screen
    -s --short                  One line output
    -v --verbose                Verbose output (i.e. debug)
    --version                   Show version

"""

__author__ = "Niclas Helbro <niclas.helbro@gmail.com>"
__version__ = "Sonar Client 0.1.2"

from docopt import docopt

import os
import sys
import socket
import json
from html.parser import HTMLParser

from libsonar import Subsonic
from libsonar import read_config
from libsonar import debug
from libsonar import pretty


class SonarClient(object):
    def __init__(self, subsonic):
        self.subsonic = subsonic.connection
        self.config = read_config()
        self.cached_results = os.path.join(self.config["sonar"]["tmp_dir"], "results.cache")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def _socket_send(self, data):
        self.socket.connect((
            self.config['server']['host'],
            int(self.config['server']['port'])
        ))

        request = json.dumps(data)
        self.socket.sendall(request.encode("utf-8"))

        response = self.socket.recv(102400)
        response = response.decode("utf-8")

        # debug(response)
        # if "code" not in response or response["code"] != "OK" and "msg" in response:
        #     debug(response["msg"])

        self.socket.close()
        return json.loads(response)

    def _format_results(self, results):
        for kind in ["artist", "album", "song"]:
            if kind in results and not isinstance(results[kind], list):
                results[kind] = [results[kind]]
        return results

    def _cache_results(self, results):
        f = open(self.cached_results, "wt+")
        f.write(json.dumps(results))
        f.close()

    def _cached_results(self):
        try:
            f = open(self.cached_results, "rt")
            results = json.loads(f.read())
            f.close()
        except:
            results = []
        return results

    def _build_server_data(self, idxs):
        res_list = self._cached_results()
        data = {
            "artist": [],
            "album": [],
            "song": []
        }

        if not res_list or len(res_list) == 0:
            print("\nNo result list found... Make a search first.\n")
            sys.exit(0)

        if len(idxs) == 0:
            idxs = range(len(res_list))

        if "artist" in res_list and len(res_list["artist"]) > 0:
            for idx in idxs:
                artist = res_list["artist"][idx]
                data["artist"].append({
                    "id": artist["id"],
                    "name": artist["name"]
                })
        if "album" in res_list and len(res_list["album"]) > 0:
            for idx in idxs:
                album = res_list["album"][idx]
                data["album"].append({
                    "id": album["id"],
                    "album": album["album"],
                    "artist": album["artist"]
                })
        if "song" in res_list and len(res_list["song"]) > 0:
            for idx in idxs:
                song = res_list["song"][idx]
                data["song"].append({
                    "id": song["id"],
                    "title": song["title"],
                    "album": song["album"],
                    "artist": song["artist"]
                })

        return data

    def _print(self, data):
        if type(data) == str:
            parser = HTMLParser()
            data = parser.unescape(data)
        print(data)

    def _print_results(self, results=None):
        if not results:
            results = self._cached_results()

        if "artist" in results and len(results["artist"]) > 0:
            self._print_artists(results["artist"])
        elif "album" in results and len(results["album"]) > 0:
            self._print_albums(results["album"])
        elif "song" in results and len(results["song"]) > 0:
            self._print_songs(results['song'])
        else:
            print("\nNo results...\n")

    def _print_artists(self, artists):
        if type(artists) == dict:
            artists = [artists]

        print()
        idx = 0
        for artist in artists:
            self._print("%s: %s" % (
                idx,
                artist['name']
            ))
            idx += 1
        print()

    def _print_albums(self, albums):
        if type(albums) == dict:
            albums = [albums]

        print()
        idx = 0
        for album in albums:
            self._print("%s: %s (%s)" % (
                idx,
                album['album'],
                album['artist']
            ))
            idx += 1
        print()

    def _print_songs(self, songs):
        if type(songs) == dict:
            songs = [songs]

        print()
        idx = 0
        for song in songs:
            self._print("%s: %s (%s) [ID: %s]" % (
                idx,
                song['title'],
                song['artist'],
                song['id']
            ))
            idx += 1
        print()

    def random(self, args):
        res = self.get_random(args)
        self._cache_results(res)
        self._print_results(res)

    def get_random(self, args):
        if "album" in args and args["album"]:
            ret = {"album": []}
            res = self.subsonic.getAlbumList(ltype="random", size=args['--limit'])
            if "album" in res["albumList"]:
                ret["album"] = res["albumList"]["album"]
        elif "song" in args and args["song"]:
            ret = {"song": []}
            res = self.subsonic.getRandomSongs(size=args["--limit"])
            if "song" in res["randomSongs"]:
                ret["song"] = res["randomSongs"]["song"]

        return self._format_results(ret)

    def search(self, args):
        res = self.get_search(args)
        self._cache_results(res)
        self._print_results(res)

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
        if "artist" in args and args["artist"]:
            kwargs["artistCount"] = args['--limit']
            res = self.subsonic.search2(query, **kwargs)
            ret = {"artist": []}
            if "artist" in res["searchResult2"]:
                ret["artist"] = res["searchResult2"]["artist"]
        elif "album" in args and args["album"]:
            kwargs["albumCount"] = args['--limit']
            res = self.subsonic.search2(query, **kwargs)
            ret = {"album": []}
            if "album" in res["searchResult2"]:
                ret["album"] = res["searchResult2"]["album"]
        elif "song" in args and args["song"]:
            kwargs["songCount"] = args['--limit']
            res = self.subsonic.search2(query, **kwargs)
            ret = {"song": []}
            if "song" in res["searchResult2"]:
                ret["song"] = res["searchResult2"]["song"]

        return self._format_results(ret)

    def currently_playing(self, args):
        request = {
            "operation": "currently_playing"
        }
        result = self._socket_send(request)

        if "--short" in args:
            if "current_song" in result and result["current_song"]:
                ct = result["current_song"]
                currently_playing_string = "%s (%s%%)" % (
                    ct["song"]["title"],
                    ct["progress"]["percent"]
                )

                if "playing" in ct and ct["playing"] == False:
                    currently_playing_string += " [Paused]"

                print(currently_playing_string)
        else:
            if "current_song" in result and result["current_song"]:
                ct = result["current_song"]
                print("\nCurrently playing: %s" % ct["song"]["title"])

                if "progress" in ct:
                    progress_string = "Progress: %(time)s / %(length)s (%(percent)s%%)" % ct["progress"]

                if "playing" in ct and ct["playing"] == False:
                    progress_string += " [Paused]"

                print("%s\n" % progress_string)
            else:
                print("\nNothing is playing...\n")

    def play(self, args):
        request = {
            "operation": "play"
        }

        # print(args)

        if "INDEX" in args and isinstance(args["INDEX"], list) and \
                len(args["INDEX"]) > 0 and isinstance(args["INDEX"][0], int):
            request["queue_index"] = args["INDEX"][0]

        self._socket_send(request)

    def pause(self):
        request = {
            "operation": "pause"
        }
        self._socket_send(request)

    def playpause(self):
        request = {
            "operation": "playpause"
        }
        self._socket_send(request)

    def stop(self):
        request = {
            "operation": "stop"
        }
        self._socket_send(request)

    def previous_song(self):
        request = {
            "operation": "previous_song"
        }
        self._socket_send(request)

    def next_song(self):
        request = {
            "operation": "next_song"
        }
        self._socket_send(request)

    def seek(self, args):
        request = {
            "operation": "seek",
            "timedelta": args["TIMEDELTA"]
        }
        self._socket_send(request)

    def show_queue(self):
        request = {
            "operation": "show_queue",
        }

        result = self._socket_send(request)

        if "queue" in result and len(result["queue"]) > 0:
            songs = []
            for item in result["queue"]:
                songs.append(item)
            self._print_results({"song": songs})
        else:
            print("\nQueue is empty.\n")

    def set_queue(self, args):
        request = {
            "operation": "set_queue",
            "data": self._build_server_data(args["INDEX"])
        }

        self._socket_send(request)

    def prepend_queue(self, args):
        request = {
            "operation": "prepend_queue",
            "data": self._build_server_data(args["INDEX"])
        }

        self._socket_send(request)

    def append_queue(self, args):
        request = {
            "operation": "append_queue",
            "data": self._build_server_data(args["INDEX"])
        }

        self._socket_send(request)

if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

    ###
    ##  Instatiate classes
    ###
    subsonic = Subsonic()
    client = SonarClient(subsonic)

    ###
    ##  Fix defaults and fallbacks
    ###
    # Default to song if neither artist nor album nor song
    # ares given in args.
    if not "artist" in args or not args["artist"] or \
            not "album" in args or not args["album"] or \
            not "song" in args or not args["song"]:
        args["song"] = True

    # Make sure args["INDEX] is a list of ints.
    if "INDEX" in args and len(args["INDEX"]) > 0:
        try:
            for idx in range(len(args["INDEX"])):
                args["INDEX"][idx] = int(args["INDEX"][idx])
        except Exception as e:
            debug(str(e))
            print("\nYou have to supply a list of integer indeces.\n")
            sys.exit(0)

    # If TIMEDELTA is in args, make sure it is an int.
    if "TIMEDELTA" in args and args["TIMEDELTA"]:
        try:
            args["TIMEDELTA"] = int(args["TIMEDELTA"])
        except Exception as e:
            debug(str(e))
            print("\nThe time delta needs to be an integer.\n")
            sys.exit(0)
    else:
        args["TIMEDELTA"] = 10

    ###
    ##  Main arg handler
    ###
    if "search" in args and args["search"]:
        client.search(args)
    elif "random" in args and args["random"]:
        client.random(args)
    elif "last" in args and args["last"]:
        client._print_results()
    elif "play" in args and args["play"]:
        client.play(args)
    elif "playpause" in args and args["playpause"] or "pp" and args["pp"]:
        client.playpause()
    elif "pause" in args and args["pause"]:
        client.pause()
    elif "stop" in args and args["stop"]:
        client.stop()
    elif "prev" in args and args["prev"]:
        client.previous_song()
    elif "next" in args and args["next"]:
        client.next_song()
    elif "rw" in args and args["rw"]:
        args["TIMEDELTA"] = -args["TIMEDELTA"]
        client.seek(args)
    elif "ff" in args and args["ff"]:
        client.seek(args)
    elif "queue" in args and args["queue"]:
        if "show" in args and args["show"]:
            client.show_queue()
        elif "clear" in args and args["clear"]:
            args["INDEX"] = []  # Make sure we are setting queue to empty
            client.set_queue(args)
        elif "set" in args and args["set"]:
            client.set_queue(args)
        elif "prepend" in args and args["set"]:
            client.prepend_queue(args)
        elif "append" in args and args["append"] or True:
            # Default to append to queue
            client.append_queue(args)
    elif "status" in args and args["status"] or True:
        # Assume the user wants to know the status of what
        # is being played at the moment.
        client.currently_playing(args)
