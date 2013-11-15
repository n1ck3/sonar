#!/usr/bin/env python3

"""
Sonar Client

Usage:
    sonar.py (search | s) [(artist|album|song) SEARCH_STRING...] [options]
    sonar.py (random | x) [album|song] [options]
    sonar.py (last | list | l) [options]
    sonar.py (play) [INDEX] [options]
    sonar.py (pause) [options]
    sonar.py (playpause | pp) [options]
    sonar.py (stop | s) [options]
    sonar.py ((previous | prev | p) | (next | n)) [options]
    sonar.py ((rewind | rw) | (fastforward | ff)) [TIMEDELTA] [options]
    sonar.py (repeat | r) [on | off] [options]
    sonar.py (queue | q) [(shuffle | x) | (sort | s)|[[(set | s)|(prepend | first | p)|(append | add | last | a)|(remove | clear | c)] INDEX...]] [options]
    sonar.py [status] [options]

Options:
    -n LIMIT, --limit LIMIT     Limit results [default: 10]
    -h --help                   Shows this screen
    -s --short                  One line output
    -sb --statusbar             JSON output that can be used by statusbars
    -v --verbose                Verbose output (i.e. show debug)
    --version                   Show version

"""

__author__ = "Niclas Helbro <niclas.helbro@gmail.com>"
__version__ = "Sonar Client 0.1.3"

from docopt import docopt

import os
import sys
import socket
import json
import datetime
from html.parser import HTMLParser

from libsonar import Subsonic
from libsonar import read_config
from libsonar import debug


class SonarClient(object):
    def __init__(self, subsonic):
        self.DEBUG = False
        self.config = read_config()
        self.tmp_dir = os.path.join(self.config["sonar"]["tmp_dir"])
        self.cache_dir = os.path.join(self.tmp_dir, "cache")
        os.makedirs(self.tmp_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)

        self.subsonic = subsonic.connection
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cached_results = os.path.join(
            self.config["sonar"]["tmp_dir"],
            "results.cache"
        )

    def _socket_send(self, data):
        if self.DEBUG:
            print("\n > Debug: %s \n" % data)

        self.socket.connect((
            self.config['server']['host'],
            int(self.config['server']['port'])
        ))

        request = json.dumps(data)
        self.socket.sendall(request.encode("utf-8"))

        response = self.socket.recv(102400)
        response = response.decode("utf-8")

        response_data = json.loads(response)
        if "message" in response_data:
            print("\n%s\n" % response_data["message"])

        self.socket.close()
        return response_data

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

        if "artist" in res_list and len(res_list["artist"]) > 0:
            if isinstance(idxs, list) and len(idxs) == 1 and idxs[0] == -1:
                idxs = []
            elif len(idxs) == 0:
                idxs = range(0, len(res_list["artist"]))

            for idx in idxs:
                artist = res_list["artist"][idx]
                data["artist"].append({
                    "id": artist["id"],
                    "name": artist["name"]
                })

        if "album" in res_list and len(res_list["album"]) > 0:
            if isinstance(idxs, list) and len(idxs) == 1 and idxs[0] == -1:
                idxs = []
            elif len(idxs) == 0:
                idxs = range(0, len(res_list["album"]))

            for idx in idxs:
                album = res_list["album"][idx]
                data["album"].append({
                    "id": album["id"],
                    'album': album["name"],  # album["album"] ?
                    "artist": album["artist"]
                })

        if "song" in res_list and len(res_list["song"]) > 0:
            if isinstance(idxs, list) and len(idxs) == 1 and idxs[0] == -1:
                idxs = []
            elif len(idxs) == 0:
                idxs = range(0, len(res_list["song"]))

            for idx in idxs:
                song = res_list["song"][idx]
                data["song"].append({
                    "id": song["id"],
                    "title": song["title"],
                    "album": song["album"],
                    "artist": song["artist"]
                })

        return data

    def _print(self, data, end="\n"):
        if type(data) == str:
            parser = HTMLParser()
            data = parser.unescape(data)
        print(data, end=end)

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
            self._print("%s: %s [ID: %s]" % (
                idx,
                artist['name'],
                artist['id']
            ))
            idx += 1
        print()

    def _print_albums(self, albums):
        if type(albums) == dict:
            albums = [albums]

        print()
        idx = 0
        for album in albums:
            album_name = album.get(
                "name",
                album.get(
                    "album",
                    "Unknown album name"
                )
            )
            self._print("%s: %s (%s) [ID: %s]" % (
                idx,
                album_name,
                album['artist'],
                album['id']
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

    def _format_time(self, secs):
        if isinstance(secs, int):
            return datetime.timedelta(seconds=secs)

    def random(self, args):
        res = self.get_random(args)
        self._cache_results(res)
        self._print_results(res)

    def get_random(self, args):
        if "album" in args and args["album"]:
            ret = {"album": []}
            res = self.subsonic.getAlbumList(
                ltype="random",
                size=args['--limit']
            )
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
            res = self.subsonic.search3(query, **kwargs)
            ret = {"artist": []}
            if "artist" in res["searchResult3"]:
                ret["artist"] = res["searchResult3"]["artist"]
        elif "album" in args and args["album"]:
            kwargs["albumCount"] = args['--limit']
            res = self.subsonic.search3(query, **kwargs)
            ret = {"album": []}
            if "album" in res["searchResult3"]:
                ret["album"] = res["searchResult3"]["album"]
        elif "song" in args and args["song"]:
            kwargs["songCount"] = args['--limit']
            res = self.subsonic.search3(query, **kwargs)
            ret = {"song": []}
            if "song" in res["searchResult3"]:
                ret["song"] = res["searchResult3"]["song"]

        return self._format_results(ret)

    def status(self, args):
        request = {
            "operation": "status"
        }
        result = self._socket_send(request)

        if "--short" in args and args["--short"]:
            if "current_song" in result and result["current_song"]:
                ct = result["current_song"]

                currently_playing_string = ct["song"]["title"]

                if "progress" in ct and ct["progress"]:
                    currently_playing_string += " (%s%%)" % (
                        ct["progress"]["percent"]
                    )

                if "player_state" in ct:
                    currently_playing_string += " [%s]" % ct["player_state"]

                self._print(currently_playing_string)
        elif "--statusbar" in args and args["--statusbar"]:
            ct = result["current_song"]
            data = {
                "song": {
                    "artist": ct["song"]["artist"],
                    "album": ct["song"]["album"],
                    "title": ct["song"]["title"],
                },
                "player": {
                    "state": ct["player_state"],
                    "repeat": ct["repeat"]
                }
            }
            if "progress" in ct and ct["progress"]:
                data["progress"] = {
                    "time": str(self._format_time(ct["progress"]["time"])),
                    "length": str(self._format_time(ct["progress"]["length"])),
                    "percent": ct["progress"]["percent"]
                }
            if "queue" in ct and ct["queue"]:
                data["queue"] = {
                    "index": ct["queue"]["index"],
                    "length": ct["queue"]["length"]
                }
            self._print(json.dumps(data), end="")
        else:
            if "current_song" in result and result["current_song"]:
                ct = result["current_song"]

                currently_playing_string = "\n%s - %s (%s)" % (
                    ct["song"]["artist"],
                    ct["song"]["title"],
                    ct["song"]["album"]
                )

                progress_list = []
                if "progress" in ct and ct["progress"]:
                    progress_list.append("%s / %s (%s%%)" % (
                        self._format_time(ct["progress"]["time"]),
                        self._format_time(ct["progress"]["length"]),
                        ct["progress"]["percent"]
                    ))

                if "player_state" in ct:
                    progress_list.append("[%s]" % ct["player_state"])

                if "repeat" in ct and ct["repeat"]:
                    progress_list.append("[Repeat]")

                self._print(currently_playing_string)

                if progress_list:
                    print("%s\n" % " ".join(progress_list))
                else:
                    print()
            else:
                # Only print "Nothing is playing" if we want verbose output
                print("\nNothing is playing...\n")

    def play(self, args):
        request = {
            "operation": "play"
        }

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

    def shuffle(self, args):
        request = {
            "operation": "shuffle"
        }

        self._socket_send(request)

    def sort_queue(self, args):
        request = {
            "operation": "sort_queue"
        }

        self._socket_send(request)

    def repeat(self, args):
        request = {
            "operation": "repeat"
        }
        if "on" in args and args["on"]:
            request["value"] = True
        elif "off" in args and args["off"]:
            request["value"] = False
        else:
            # Toggle repeat plz.
            request["value"] = None

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

        if "queue" in result and \
                isinstance(result["queue"], list) and \
                len(result["queue"]) > 0:
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

    def remove_from_queue(self, args):
        request = {
            "operation": "remove_from_queue",
            "data": args["INDEX"]
        }

        self._socket_send(request)


if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

    ###
    ##  Instatiate classes
    ###
    subsonic = Subsonic()
    client = SonarClient(subsonic)
    if "--verbose" in args and args["--verbose"]:
        client.DEBUG = True

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
    if "search" in args and args["search"] or \
            "s" in args and args["s"]:
        client.search(args)
    elif "random" in args and args["random"] or \
            "x" in args and args["x"]:
        client.random(args)
    elif "list" in args and args["list"] or \
            "last" in args and args["last"] or \
            "l" in args and args["l"]:
        client._print_results()
    elif "play" in args and args["play"]:
        client.play(args)
    elif "pause" in args and args["pause"]:
        client.pause()
    elif "playpause" in args and args["playpause"] or \
            "pp" and args["pp"]:
        client.playpause()
    elif "stop" in args and args["stop"] or \
            "s" and args["s"]:
        client.stop()
    elif "previous" in args and args["previous"] or \
            "prev" in args and args["prev"] or \
            "p" and args["p"]:
        client.previous_song()
    elif "next" in args and args["next"] or \
            "n" and args["n"]:
        client.next_song()
    elif "repeat" in args and args["repeat"] or \
            "r" and args["r"]:
        client.repeat(args)
    elif "rewind" in args and args["rewind"] or \
            "rw" in args and args["rw"]:
        args["TIMEDELTA"] = -args["TIMEDELTA"]
        client.seek(args)
    elif "fastforward" in args and args["fastforward"] or \
            "ff" in args and args["ff"]:
        client.seek(args)
    elif "queue" in args and args["queue"] or \
            "q" in args and args["q"]:
        if "shuffle" in args and args["shuffle"] or \
                "x" in args and args["x"]:
            client.shuffle(args)
        elif "sort" in args and args["sort"] or \
                "o" in args and args["o"]:
            client.sort_queue(args)
        elif "set" in args and args["set"] or \
                "s" in args and args["s"]:
            client.set_queue(args)
        elif "prepend" in args and args["prepend"] or \
                "first" in args and args["first"] or \
                "p" in args and args["p"]:
            client.prepend_queue(args)
        elif "append" in args and args["append"] or \
                "add" in args and args["add"] or \
                "last" in args and args["last"] or \
                "a" in args and args["a"]:
            client.append_queue(args)
        elif "remove" in args and args["remove"] or \
                "clear" in args and args["clear"] or \
                "c" in args and args["c"]:
            if "INDEX" in args and len(args["INDEX"]) == 0:
                args["INDEX"] = [-1]  # Make sure we are setting queue to empty
            client.remove_from_queue(args)
        else:
            # Default to show queue
            client.show_queue()
    elif "status" in args and args["status"] or True:
        # Assume the user wants to know the status of what
        # is being played at the moment.
        client.status(args)
