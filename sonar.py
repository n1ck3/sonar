#!/usr/bin/env python3

"""
Sonar Client

Usage:
    sonar.py search [artist | album | song] (SEARCH_STRING...) [options]
    sonar.py playlists [options]
    sonar.py cached [options]
    sonar.py random [album | song] [options]
    sonar.py last [options]
    sonar.py play [INDEX...] [options]
    sonar.py (pause | p) [options]
    sonar.py stop [options]
    sonar.py (previous | next) [options]
    sonar.py (rw | ff) [TIMEDELTA] [options]
    sonar.py (queue | q) [
        repeat [on | off] |
        shuffle |
        sort |
        (set | prepend | add | remove) [INDEX...]
    ] [options]
    sonar.py [status] [options]

Options:
    -n LIMIT, --limit LIMIT     Limit results [default: 10]
    -h --help                   Shows this screen
    -s --short                  One line output
    -sb --statusbar             JSON output that can be used by statusbars
    -l --loglevel LOGLEVEL      Set the loglevel [default: warning]
                                (critical | error | warning | info | debug)
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
import logging
import glob
from html.parser import HTMLParser

from libsonar import Subsonic
from libsonar import read_config


LOGFORMAT = '%(asctime)s %(levelname)s - %(message)s'
logging.basicConfig(
    format=LOGFORMAT,
    datefmt='%m-%d %H:%M'
)
logger = logging.getLogger(__name__)


class SonarClient(object):
    def __init__(self, subsonic):
        self.config = read_config()

        self.sonar_dir = os.path.join(self.config["sonar"]["sonar_dir"])
        os.makedirs(self.sonar_dir, exist_ok=True)

        self.cache_dir = os.path.join(self.sonar_dir, "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

        self.subsonic = subsonic.connection
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.cached_results = os.path.join(self.sonar_dir, "results.cache")

    def _socket_send(self, data):

        self.socket.connect((
            self.config['server']['host'],
            int(self.config['server']['port'])
        ))

        request = json.dumps(data)
        self.socket.sendall(request.encode("utf-8"))
        logger.debug("Sent data: %s" % data)

        response = self.socket.recv(102400)
        response = response.decode("utf-8")

        response_data = json.loads(response)
        logger.debug("Received data: %s" % response_data)
        if "message" in response_data:
            print("\n%s\n" % response_data["message"])

        self.socket.close()
        return response_data

    def _format_results(self, results):
        for kind in ["artist", "album", "song", "playlists"]:
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

    def _cached_songs(self):
        cached_paths = glob.glob(os.path.join(client.cache_dir, "*.mp3"))
        return [os.path.basename(x).replace(".mp3", "") for x in cached_paths]

    def _build_server_data(self, idxs):
        res_list = self._cached_results()
        data = {
            "artist": [],
            "album": [],
            "song": [],
            "playlists": []
        }

        if not res_list or len(res_list) == 0:
            print("\nNo result list found... Make a search first.\n")
            sys.exit(1)

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
                if album.get("title"):
                    # Random albums have a title.
                    album_name = album["title"]
                elif album.get("name"):
                    # Otherwise its called name.
                    album_name = album["name"]
                else:
                    # Or die.
                    print("Could not get album name...")
                    sys.exit(1)

                data["album"].append({
                    "id": album["id"],
                    'album': album_name,
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

        if "playlists" in res_list and len(res_list["playlists"]) > 0:
            logger.info("playlist")
            if isinstance(idxs, list) and len(idxs) == 1 and idxs[0] == -1:
                idxs = []
            elif len(idxs) == 0:
                idxs = range(0, len(res_list["playlist"]))

            for idx in idxs:
                playlist = res_list["playlists"][idx]
                data["playlists"].append({
                    "id": playlist["id"],
                    'playlist': playlist["name"]
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
        elif "queue" in results and len(results["queue"]) > 0:
            self._print_queue(
                results['queue'],
                results.get("current_song", 0),
                results.get("player_state", None)
            )
        elif "playlists" in results and len(results["playlists"]) > 0:
            self._print_playlists(results['playlists'])
        else:
            print("\nNo results...\n")

    def _print_artists(self, artists):
        if type(artists) == dict:
            artists = [artists]

        print(self._colorize("\n* Artists *\n", "white"))
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

        print(self._colorize("\n* Albums *\n", "white"))
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

        print(self._colorize("\n* Songs *\n", "white"))

        cached_songs = self._cached_songs()
        idx = 0
        for song in songs:
            song_string = "%s: %s (%s) [ID: %s]" % (
                idx,
                song['title'],
                song['artist'],
                song['id']
            )
            if str(song['id']) in cached_songs:
                song_string += " %s" % self._colorize("*", "green")
            self._print(song_string)
            idx += 1
        print()

    def _print_queue(self, songs, current_song=None, player_state=None):
        if type(songs) == dict:
            songs = [songs]

        print(self._colorize("\n* Queue *\n", "white"))

        cached_songs = self._cached_songs()
        idx = 0
        for song in songs:
            song_string = "%s: %s (%s) [ID: %s]" % (
                idx,
                song['title'],
                song['artist'],
                song['id']
            )

            # Bells and whistles: Highlight current song in queue and colorize
            # if player_state is paused or playing.
            if current_song == idx:
                color = "white"
                if player_state == "Paused":
                    color = "yellow"
                elif player_state == "Playing":
                    color = "green"

                song_string = self._colorize(song_string, color)

            if str(song['id']) in cached_songs:
                song_string += " %s" % self._colorize("*", "green")

            self._print(song_string)
            idx += 1
        print()

    def _print_playlists(self, playlists):
        print(self._colorize("\n* Playlist *\n", "white"))
        idx = 0
        for playlist in playlists:
            self._print("%s: %s (%s) [ID: %s]" % (
                idx,
                playlist['name'],
                playlist['songCount'],
                playlist['id']
            ))
            idx += 1
        print()

    def _format_time(self, secs):
        if isinstance(secs, int):
            return datetime.timedelta(seconds=secs)

    def _colorize(self, string="", color=None):
        colors = {
            "red": "\033[1;91m",
            "green": "\033[1;92m",
            "yellow": "\033[1;93m",
            "magenta": "\033[1;95m",
            "white": "\033[1;97m"
        }
        end_code = "\033[0m"
        color_code = colors.get(color, end_code)

        return "%s%s%s" % (color_code, string, end_code)

    def random(self, args):
        res = self.get_random(args)
        self._cache_results(res)
        self._print_results(res)

    def get_random(self, args):
        if "album" in args and args["album"]:
            ret = {"album": []}
            res = self.subsonic.getAlbumList2(
                ltype="random",
                size=args['--limit']
            )
            if "album" in res["albumList2"]:
                ret["album"] = res["albumList2"]["album"]
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

    def list_cached_songs(self, args):
        res = self.get_cached_songs(args)
        self._cache_results(res)
        self._print_results(res)

    def get_cached_songs(self, args):
        tag_data_map = {
            "title": (3, 33),
            "artist": (33, 63),
            "album": (63, 93),
        }
        cached_songs = []
        for song_path in glob.glob(os.path.join(client.cache_dir, "*.mp3")):
            song_id = os.path.basename(song_path).replace(".mp3", "")
            try:
                with open(song_path, "rb", 0) as song_file:
                    try:
                        song_file.seek(-128, 2)
                        tag_data = song_file.read(128)
                    finally:
                        song_file.close()

                    if tag_data[:3] == b"TAG":
                        song_dict = {"id": song_id}
                        for tag, (start, end) in tag_data_map.items():
                            song_dict[tag] = tag_data[start:end].decode(
                                "utf-8", "replace").replace("\x00", "").strip()
                        cached_songs.append(song_dict)
            except IOError:
                # Something went wrong getting ID3 tag data,
                # just skip this song.
                pass

        ret = {"song": cached_songs}
        return self._format_results(ret)

    def list_playlists(self, args):
        res = self.get_playlists(args)
        self._cache_results(res)
        self._print_results(res)

    def get_playlists(self, args):
        res = self.subsonic.getPlaylists()
        ret = {"playlists": res.get("playlists", {}).get("playlist", [])}
        return self._format_results(ret)

    def status(self, args):
        request = {
            "operation": "status"
        }
        result = self._socket_send(request)

        if "--short" in args and args["--short"]:
            if "current_song" in result and result["current_song"]:
                ct = result["current_song"]

                currently_playing_string = "[%s/%s] %s" % (
                    ct["queue_position"],
                    ct["queue_length"],
                    ct["song"]["title"]
                )

                progress_list = []
                if ct.get("downloading"):
                    # If Downloading, we do not want to show any other player
                    # info.
                    progress_list.append(self._colorize(
                        "Downloading",
                        "magenta"
                    ))
                else:
                    # Ok, not Downloading, show some player info.
                    if ct.get("progress"):
                        currently_playing_string += " (%s%%)" % (
                            ct["progress"]["percent"]
                        )

                    if ct.get("player_state"):
                        if ct["player_state"] == "Stopped":
                            color = "red"
                        elif ct["player_state"] == "Paused":
                            color = "yellow"
                        elif ct["player_state"] == "Playing":
                            color = "green"
                        progress_list.append(
                            self._colorize(
                                ct["player_state"],
                                color
                            )
                        )

                if ct.get("repeat"):
                    progress_list.append("R")

                if ct.get("shuffle"):
                    progress_list.append("S")

                currently_playing_string += " | %s" % " | ".join(
                    progress_list
                )

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
                    "queue_position": ct["queue_position"],
                    "queue_lenght": ct["queue_length"],
                    "state": ct["player_state"],
                    "repeat": ct["repeat"],
                    "shuffle": ct["shuffle"],
                    "downloading": ct["downloading"]
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

                currently_playing_string = "\n[%s/%s] %s - %s (%s)" % (
                    ct["queue_position"],
                    ct["queue_length"],
                    ct["song"]["artist"],
                    ct["song"]["title"],
                    ct["song"]["album"]
                )

                progress_list = []
                if ct.get("downloading"):
                    # If Downloading, we do not want to show any other player
                    # info.
                    progress_list.append(self._colorize(
                        "Downloading",
                        "magenta"
                    ))
                else:
                    # Ok, not Downloading, show some player info.
                    if ct.get("player_state"):
                        if ct["player_state"] == "Stopped":
                            color = "red"
                        elif ct["player_state"] == "Paused":
                            color = "yellow"
                        elif ct["player_state"] == "Playing":
                            color = "green"
                        progress_list.append(
                            self._colorize(
                                ct["player_state"],
                                color
                            )
                        )

                    if "progress" in ct and ct["progress"]:
                        progress_list.append("%s / %s (%s%%)" % (
                            self._format_time(ct["progress"]["time"]),
                            self._format_time(ct["progress"]["length"]),
                            ct["progress"]["percent"]
                        ))

                if ct.get("repeat"):
                    progress_list.append("Repeat")

                if ct.get("shuffle"):
                    progress_list.append("Shuffle")

                self._print(currently_playing_string)

                if progress_list:
                    print("%s\n" % " | ".join(progress_list))
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
            self._print_results({
                "queue": songs,
                "current_song": result.get("current_song", 0),
                "player_state": result.get("player_state", None)
            })

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
    ## Set loglevel
    ###
    loglevels = ["critical", "error", "warning", "info", "debug"]
    if "--loglevel" in args and args["--loglevel"] in loglevels:
        logger.setLevel(getattr(logging, args["--loglevel"].upper()))
    else:
        logger.critical("Invalid loglevel. Exiting...")
        sys.exit(1)

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
            logger.debug(str(e))
            print("\nYou have to supply a list of integer indeces.\n")
            sys.exit(1)

    # If TIMEDELTA is in args, make sure it is an int.
    if "TIMEDELTA" in args and args["TIMEDELTA"]:
        try:
            args["TIMEDELTA"] = int(args["TIMEDELTA"])
        except Exception as e:
            logger.debug(str(e))
            print("\nThe time delta needs to be an integer.\n")
            sys.exit(1)
    else:
        args["TIMEDELTA"] = 10

    ###
    ##  Main arg handler
    ###
    if args.get("search", False):
        client.search(args)
    elif args.get("cached", False):
        client.list_cached_songs(args)
    elif args.get("playlists", False):
        client.list_playlists(args)
    elif args.get("random"):
        client.random(args)
    elif args.get("last"):
        client._print_results()
    elif args.get("play"):
        client.play(args)
    elif args.get("pause") or args.get("p"):
        client.pause()
    elif args.get("stop"):
        client.stop()
    elif args.get("previous"):
        client.previous_song()
    elif args.get("next"):
        client.next_song()
    elif args.get("rw"):
        args["TIMESELTA"] = -args.get("TIMEDELTA", 5)
        client.seek(args)
    elif args.get("ff"):
        client.seek(args)
    elif args.get("queue") or args.get("q"):
        if args.get("shuffle"):
            client.shuffle(args)
        elif args.get("repeat"):
            client.repeat(args)
        elif args.get("sort"):
            client.sort_queue(args)
        elif args.get("set"):
            client.set_queue(args)
        elif args.get("prepend"):
            client.prepend_queue(args)
        elif args["add"]:
            client.append_queue(args)
        elif args.get("remove"):
            args["INDEX"] = args.get("INDEX", [])
            if len(args["INDEX"]) == 0:
                # Make sure we are setting queue to empty
                args["INDEX"] = [-1]
            client.remove_from_queue(args)
        else:
            # Default to show queue
            client.show_queue()
    elif args.get("status") or True:
        # Assume the user wants to know the status of what
        # is being played at the moment.
        client.status(args)
