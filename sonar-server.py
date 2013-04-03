#!/usr/bin/env python3

"""
Sonar Server

Usage:
    sonar-server.py

    sonar-server.py (-h | --help)
    sonar-server.py (-v | --verbose)
    sonar-server.py --version

Options:
    -h --help                   Shows this screen
    -v --verbose                Verbose output (i.e. show debug)
    --version                   Show version

"""

__author__ = "Niclas Helbro <niclas.helbro@gmail.com>"
__version__ = "Sonar Server 0.1.3"

from docopt import docopt

import os
import sys
import time
import socket
import json
import threading
from queue import Queue

from libsonar import Subsonic
from libsonar import read_config
from libsonar import debug
from libsonar import pretty

from mplayer import Player as MPlayer

msg_queue = Queue(1)

class SonarServer(object):
    def __init__(self, msg_queue):
        self.config = read_config()

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("", int(self.config['server']['port'])))
            self.socket.listen(1)
            self.socket.setblocking(0)
            self.socket_is_open = True
        except OSError as e:
            print("\nCould not start server socket.")
            print("%s\n" % e)
            sys.exit(0)

        self.cache_dir = os.path.join(self.config["sonar"]["tmp_dir"], "cache")


        subsonic = Subsonic()
        self.subsonic = subsonic.connection
        self.player = PlayerThread(subsonic, msg_queue)

        self.current_song = None
        self.queue = []

        self.shuffle = False
        self.repeat = False

        self.msg_queue = msg_queue

    def _start_server(self):
        debug("Starting server")

        operations = (
            "status",
            "play",
            "pause",
            "playpause",
            "stop",
            "previous_song",
            "next_song",
            "seek",
            "repeat",
            "shuffle",
            "set_queue",
            "prepend_queue",
            "append_queue",
            "show_queue"
        )

        while self.socket_is_open:
            print("WHILE")
            # Check if the queue has something for us.
            if not self.msg_queue.empty():
                msg = self.msg_queue.get()
                # Figure out what to do with the queue message.
                if msg == "EOF":
                    # Done playing a file? Play the next in the queue.
                    self.play_next_song()

            try:
                # Try to get connection and address of client.
                conn, addr = self.socket.accept()
            except Exception as e:
                # Client has not sent a request. Set connection to none so
                # that we can avoid trying to handle the request later.
                conn = None

            if conn:
                print("Conn")
                # There is a connection made by the client in this iteration!
                debug("Connected by %s (pid: %s)" % addr)
                data = conn.recv(102400)

                try:
                    # Try to handle the request.
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
                            if operation == "status":
                                ret['current_song'] = self.status()

                            elif operation == "play":
                                if "queue_index" in request:
                                    success, msg = self.play(queue_index=int(request["queue_index"]))
                                    if not success:
                                        ret["code"] = "ERROR"
                                        ret["message"] = msg

                                else:
                                    success, msg = self.play()
                                    if not success:
                                        ret["code"] = "ERROR"
                                        ret["message"] = msg

                            elif operation in ["pause"]:
                                self.pause()

                            elif operation in ["playpause"]:
                                self.playpause()

                            elif operation == "stop":
                                self.stop()

                            elif operation == "next_song":
                                self.play_next_song()

                            elif operation == "previous_song":
                                self.play_previous_song()

                            elif operation == "shuffle":
                                value = None
                                if "value" in request:
                                    value = request["value"]
                                self.set_shuffle(value=value)

                            elif operation == "repeat":
                                value = None
                                if "value" in request:
                                    value = request["value"]
                                self.set_repeat(value=value)

                            elif operation == "seek" and "timedelta" in request:
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
                            # The request operation was not found in the list of
                            # permitted operations. Go bananas.
                            raise Exception("Operation not permitted.")

                    else:
                        # "operation" not in request. You know the drill.
                        raise Exception("No operation given.")


                    # Send the response to the client.
                    response = json.dumps(ret)
                    debug("Returning response: %s" % response)
                    conn.sendall(response.encode("utf-8"))

                    conn.close()

                except Exception as e:
                    # Exception handler for request handler logic.
                    print(e)
                    ret = {
                        "code": "ERROR",
                        "message": str(e)
                    }
                    raise

            else:
                # Wait for a little before starting to listen to socket connection again
                time.sleep(1)

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


    def _get_song_from_queue(self, index):
        ret = None
        if isinstance(self.current_song, int) and 0 <= index < len(self.queeu):
            ret = self.queue[index]

        return ret

    def _get_current_song(self):
        return self._get_song_from_queue(self.current_song)

    def _get_previous_song(self):
        return self._get_song_from_queue(self.current_song-1)

    def _get_next_song(self):
        return self._get_song_from_queue(self.current_song+1)

    def _play_song_by_song(self, song=None):
        # No usecase yet.
        if not self.queue:
            # Just return if there is no queue
            return False, "Can't play if there is no queue."

        if song and "id" in song:
            song_id = song["id"]
            s_id = None
            for idx, s in enumerate(self.queue):
                if "id" in s and s["id"] == song_id:
                    self.current_song = idx
            if s_id:
                self.player.play(s_id)
                return True, ""

        return False, "The song is not in the queue: %s" % song

    def _play_song_by_queue_index(self, queue_index=None):
        if not self.queue:
            # Just return if there is no queue
            return False, "Can't play if there is no queue."

        if isinstance(queue_index, int) and queue_index >= 0 and queue_index < len(self.queue):
            self.current_song = queue_index
            s_id = self.queue[queue_index]["id"]
            self.player.play(s_id)
            return True, ""

        return False, "Index not in queue: %s" % queue_index

    def _play_song_by_song_id(self, song_id=None):
        # No usecase yet.
        if not self.queue:
            # Just return if there is no queue
            return False, "Can't play if there is no queue."

        if song_id and isinstance(song_id, int):
            s_id = None
            for idx, s in enumerate(self.queue):
                if "id" in s and s["id"] == song_id:
                    self.current_song = idx
            if s_id:
                self.player.play(s_id)
                return True, ""

        return False, "There is no song in the queue with the song_id: %s" % song_id

    def status(self):
        if not isinstance(self.current_song, int):
            return None

        ret = {
            "song": self.queue[self.current_song],
            "playing": self.player.playing(),
            "progress": self.player.progress(),
            "shuffle": self.shuffle,
            "repeat": self.repeat
        }

        return ret

    def play(self, queue_index=None):
        print("in play")
        if isinstance(queue_index, int):
            print("is int: %s" % queue_index)
            return self._play_song_by_queue_index(queue_index=queue_index)

        elif self.player.playing():
            # Return silently if player is already playing
            return True, ""

        elif self.player.filename() and not self.player.playing():
            # If player is paused If there is already a song playing. Press play.
            self.player.playpause()

        elif len(self.queue) > 0:
            # OK then. Nothing is playing, let's play
            # the first song in the queue.
            # self.current_song = 0
            if not self.current_song:
                self.current_song = 0
            self._play_song_by_queue_index(queue_index=self.current_song)
            return True, ""

        # No queue. Return sadness.
        return False, "Can't play if there is no queue."

    def play_previous_song(self):
        if self.queue and isinstance(self.current_song, int):
            queue_index = self.current_song-1
            if queue_index and isinstance(queue_index, int):
                if queue_index < 0:
                    if self.repeat:
                        queue_index = len(self.queue)-1
                    else:
                        queue_index = 0
                    self._play_song_by_queue_index(queue_index=queue_index)
                    return True, ""
                elif queue_index > len(self.queue)-1:
                    queue_index = 0
                    if not self.repeat:
                        self.stop()
                        return False, "Could not play next song."
                    self._play_song_by_queue_index(queue_index=queue_index)
                    return True, ""

    def play_next_song(self):
        if self.queue and isinstance(self.current_song, int):
            queue_index = self.current_song+1
            print(queue_index)
            if queue_index and isinstance(queue_index, int):
                print("in hehe")
                print(len(self.queue)-1)

                if queue_index < 0:
                    print("<0")
                    if self.repeat:
                        queue_index = len(self.queue)-1
                    else:
                        queue_index = 0

                elif queue_index > len(self.queue)-1:
                    print("<len")
                    queue_index = 0
                    if not self.repeat:
                        self.stop()
                        return False, "Could not play next song."
                self._play_song_by_queue_index(queue_index=queue_index)
                return True, ""

    def pause(self):
        if self.player.playing():
            self.player.playpause()

    def playpause(self):
        self.player.playpause()

    def stop(self):
        self.player.stop()
        # self.current_song = None
        # self.queue = []

    def set_shuffle(self, value):
        if not value:
            self.shuffle = not self.shuffle
        else:
            self.shuffle = value

    def set_repeat(self, value):
        if not value:
            self.repeat = not self.repeat
        else:
            self.repeat = value

    def seek(self, timedelta):
        if self.player.filename():
            self.player.seek(timedelta)

    def set_queue(self, data):
        self.stop()
        self.queue = self._build_queue(data)
        self.current_song = None

    def prepend_queue(self, data):
        self.queue = self._build_queue(data) + self.queue

    def append_queue(self, data):
        self.queue += self._build_queue(data)

class PlayerThread(threading.Thread):
    def __init__(self, subsonic, msg_queue):
        self.config = read_config()
        self.cache_dir = os.path.join(self.config["sonar"]["tmp_dir"], "cache")

        subsonic = Subsonic()
        self.subsonic = subsonic.connection
        self.mplayer = MPlayer(args=("-really-quiet", "-msglevel", "global=6"))
        self.mplayer.stdout.connect(self._handle_data)

        self.msg_queue = msg_queue

        super(PlayerThread, self).__init__()

    def _handle_data(self, data):
        # Handle the stdout stream coming back from MPlayer.
        if data.startswith('EOF code:'):
            # So the file has finished playing? Let the server know!
            self.msg_queue.put("EOF")

    def _get_stream(self, song_id):
        return self.subsonic.download(song_id)

    def progress(self):
        ret = None
        if self.mplayer.time_pos:
            ret = {
                "percent": self.mplayer.percent_pos,
                "time": int(self.mplayer.time_pos),
                "length": int(self.mplayer.length),
            }
        return ret

    def play(self, song_id):
        print("play")
        song_file = os.path.join(self.cache_dir, "%s" % song_id)

        # If not already cached. Download it.
        if not os.path.exists(song_file):
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            stream = self._get_stream(song_id)
            f = open(song_file, "wb")
            f.write(stream.read())
            f.close()

        print("song file:")
        print(song_file)

        self.mplayer.stop()
        time.sleep(0.05)
        self.mplayer.loadfile(song_file)
        time.sleep(0.05)
        self.mplayer.pause()

    def playing(self):
        # A little hacky but MPlayer().paused does not
        # return what would be expected.
        playing = False
        time1 = self.mplayer.time_pos
        time.sleep(0.05)
        time2 = self.mplayer.time_pos
        if time1 != time2:
            playing = True

        return playing

    def playpause(self):
        print("playpause")
        self.mplayer.pause()

    def stop(self):
        self.mplayer.stop()

    def seek(self, timedelta):
        if self.mplayer.filename and isinstance(timedelta, int):
            time_pos = self.mplayer.time_pos
            length = self.mplayer.length
            new_time_pos = time_pos + timedelta
            if new_time_pos < 0:
                new_time_pos = 0
            elif new_time_pos > length:
                new_time_pos = length - 1

            self.mplayer.time_pos = new_time_pos

    def filename(self):
        return self.mplayer.filename

if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

    server = SonarServer(msg_queue)
    server._start_server()

    # if "search" in args and args["search"]:
    #     client.get_search(args)
    # elif "random" in args and args["random"]:
    #     client.get_random(args)
    # elif "play" in args and args["play"]:
    #     player.play(song_id=args["SONG_ID"])
    # elif "shell" in args and args["shell"]:
    #     client.shell()
