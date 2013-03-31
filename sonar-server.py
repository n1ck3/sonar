#!/usr/bin/env python3

"""
sonar.

Usage:
    sonarserver.py

    sonarserver.py (-h | --help)
    sonarserver.py (-v | --verbose)
    sonarserver.py --version

Options:
    -h --help                   Shows this screen
    -v --verbose                Verbose output (i.e. debug)
    --version                   Show version

"""

__author__ = "Niclas Helbro <niclas.helbro@gmail.com>"
__version__ = "Sonar Server 0.1.1"

from docopt import docopt

import os
import sys
from time import sleep
import socket
import json
import threading

from libsonar import Subsonic
from libsonar import read_config
from libsonar import debug
from libsonar import pretty

from mplayer import Player as MPlayer

class SonarServer(object):
    def __init__(self):
        self.config = read_config()

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("", int(self.config['server']['port'])))
            self.socket.listen(1)
            self.socket_is_open = True
        except OSError as e:
            print("\nCould not start server socket.")
            print("%s\n" % e)
            sys.exit(0)

        self.cache_dir = os.path.join(self.config["sonar"]["tmp_dir"], "cache")

        subsonic = Subsonic()
        self.subsonic = subsonic.connection
        self.player = PlayerThread(subsonic)

        self.current_song = None
        self.queue = []


    def _start_server(self):
        debug("Ready for connection")

        operations = (
            "currently_playing", "play", "pause", "playpause", "stop",
            "next_song", "seek", "set_queue", "prepend_queue", "append_queue",
            "show_queue"
        )

        while self.socket_is_open:
            conn, addr = self.socket.accept()
            debug("Connected by %s (pid: %s)" % addr)
            while True:
                data = conn.recv(102400)

                if not data:
                    break

                try:
                    data = str(data.decode("utf-8"))
                    debug("Got request: %s" % data)
                    request = json.loads(data)
                    if "operation" in request:
                        if request['operation'] in operations:
                            # Success. Carry out the operation.
                            ret = {
                                "code": "OK"
                            }

                            operation = request["operation"]
                            if operation == "currently_playing":
                                ret['current_song'] = self.currently_playing()

                            elif operation == "play":
                                if "data" in request:
                                    self.set_queue(request["data"])
                                    self.play(forceplay=True)
                                else:
                                    playing = self.play()
                                    if not playing:
                                        ret["message"] = "Cannot play, queue is empty."

                            elif operation in ["pause"]:
                                self.pause()

                            elif operation in ["playpause"]:
                                self.playpause()

                            elif operation == "stop":
                                self.stop()

                            elif operation == "next_song":
                                self.next_song()

                            elif operation == "seek":
                                self.seek(request["timedelta"])

                            elif operation == "set_queue" and "data" in request:
                                self.set_queue(request["data"])

                            elif operation == "prepend_queue" and "data" in request:
                                self.prepend_queue(request["data"])

                            elif operation == "append_queue" and "data" in request:
                                self.append_queue(request["data"])

                            elif operation == "show_queue":
                                ret['queue'] = self.queue

                        else:
                            raise Exception("Operation not permitted.")

                    else:
                        raise Exception("No operation given.")

                except Exception as e:
                    print(e)
                    ret = {
                        "code": "ERROR",
                        "message": str(e)
                    }

                    conn.close()
                    raise

                response = json.dumps(ret)
                debug("Returning response: %s" % response)
                conn.sendall(response.encode("utf-8"))

            conn.close()
            sleep(0.1)

    def _stop_server(self):
        # Stop players and threads and whatnot
        self.socket_is_open = False
        self.mplayer.close()
        sys.exit(0)

    def _build_queue(self, data):
        queue = []
        artists = data.get("artist", [])
        albums = data.get("album", [])
        songs = data.get("song", [])

        if len(artists) > 0:
            for a in artists:
                try:
                    result = self.subsonic.getArtist(a["id"])
                except:
                    debug("ERROR: Could not find artist: %s" % a["id"])
                    continue

                artist = {}
                if "artist" in result:
                    artist = result["artist"]

                if artist and not "album" in artist:
                    artist = {
                        "album": [artist]
                    }

                for album in artist["album"]:
                    albums.append({"id": album["id"]})

        if len(albums) > 0:
            for a in albums:
                print("doing album: %s" % a["id"])
                try:
                    result = self.subsonic.getAlbum(a["id"])
                    print(result)
                except:
                    debug("ERROR: Could not find album: %s" % a["id"])
                    continue

                album = {}
                if "album" in result:
                    album = result["album"]

                if not "song" in album:
                    album["song"] = []
                elif not isinstance(album["song"], list):
                    album["song"] = [album["song"]]

                queue += album["song"]

        if len(songs) > 0:
            for s in songs:
                try:
                    result = self.subsonic.getSong(s["id"])
                except:
                    debug("ERROR: Could not find song: %s" % s["id"])
                    continue

                if "song" in result:
                    queue.append(result["song"])

        return queue

    def currently_playing(self):
        if not self.current_song:
            return None

        ret = {
            "song": self.current_song,
            "playing": self.player.playing(),
            "progress": self.player.progress()
        }

        return ret

    def play(self, forceplay=False):
        if not forceplay and self.player.playing():
            # Return silently if player is already playing
            return True

        elif self.player.filename() and not self.player.playing():
            # If there is already a song playing. Press play.
            self.player.playpause()

        elif len(self.queue) > 0:
            # OK then. Nothing is playing, let's play
            # the first song in the queue.
            self.current_song = self.queue[0]
            self.player.play(self.current_song["id"])
            return True

        # No queue. Return sadness.
        return False

    def pause(self):
        if self.player.playing():
            self.player.pause()

    def playpause(self):
        self.player.pause()

    def stop(self):
        self.player.stop()
        self.current_song = None
        self.queue = []

    def seek(self, timedelta):
        if self.player.playing():
            self.player.seek(timedelta)

    def next_song(self):
        self.player.next_song()

    def set_queue(self, data):
        self.stop()
        self.queue = self._build_queue(data)
        self.current_song = None

    def prepend_queue(self, data):
        self.queue = self._build_queue(data) + self.queue

    def append_queue(self, data):
        self.queue += self._build_queue(data)

class PlayerThread(threading.Thread):
    def __init__(self, subsonic):
        self.config = read_config()
        self.cache_dir = os.path.join(self.config["sonar"]["tmp_dir"], "cache")
        subsonic = Subsonic()
        self.subsonic = subsonic.connection
        self.mplayer = MPlayer(args=("-really-quiet", "-msglevel", "global=6"))
        super(PlayerThread, self).__init__()

    def _get_stream(self, song_id):
        return self.subsonic.download(song_id)

    def progress(self):
        return {
            "percent": self.mplayer.percent_pos,
            "time": int(self.mplayer.time_pos),
            "length": int(self.mplayer.length),
        }

    def play(self, song_id):
        song_file = os.path.join(self.cache_dir, "%s.mp3" % song_id)

        # If not already cached. Download it.
        if not os.path.exists(song_file):
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            stream = self._get_stream(song_id)
            f = open(song_file, "wb")
            f.write(stream.read())
            f.close()

        self.mplayer.loadfile(song_file)
        sleep(0.05)
        self.mplayer.pause()

        # TODO: check every second if is alive. Otherwise play next.
        # while self.mplayer.time_pos != None:
        #     print(int(self.mplayer.time_pos))
        #     sleep(1)
        # self.mplayer.stop()

    def playing(self):
        # A little hacky but MPlayer().paused does not
        # return what would be expected.
        playing = False
        time1 = self.mplayer.time_pos
        sleep(0.05)
        time2 = self.mplayer.time_pos
        if time1 != time2:
            playing = True

        return playing

    def pause(self):
        self.mplayer.pause()

    def stop(self):
        self.mplayer.stop()

    def seek(self, timedelta):
        if isinstance(timedelta, int):
            self.mplayer.time_pos += timedelta

    def filename(self):
        return self.mplayer.filename

if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

    server = SonarServer()
    server._start_server()

    # if "search" in args and args["search"]:
    #     client.get_search(args)
    # elif "random" in args and args["random"]:
    #     client.get_random(args)
    # elif "play" in args and args["play"]:
    #     player.play(song_id=args["SONG_ID"])
    # elif "shell" in args and args["shell"]:
    #     client.shell()
