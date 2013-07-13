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
from operator import itemgetter
from random import shuffle
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
        self.cache_dir = os.path.join(self.config["sonar"]["tmp_dir"], "cache")
        os.makedirs(self.cache_dir, exist_ok=True)

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
            "sort_queue",
            "set_queue",
            "prepend_queue",
            "append_queue",
            "remove_from_queue",
            "show_queue"
        )

        while self.socket_is_open:
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
                                queue_index = request.get("queue_index", 0)
                                threading.Thread(
                                    target=self.play,
                                    args=(queue_index,)
                                ).start()

                            elif operation in ["pause"]:
                                threading.Thread(target=self.pause).start()

                            elif operation in ["playpause"]:
                                threading.Thread(target=self.playpause).start()

                            elif operation == "stop":
                                threading.Thread(target=self.stop).start()

                            elif operation == "previous_song":
                                threading.Thread(target=self.play_previous_song).start()

                            elif operation == "next_song":
                                threading.Thread(target=self.play_next_song).start()

                            elif operation == "shuffle":
                                threading.Thread(target=self.shuffle_queue).start()

                            elif operation == "sort_queue":
                                threading.Thread(target=self.sort_queue).start()

                            elif operation == "repeat":
                                value = request.get("value", None)
                                threading.Thread(
                                    target=self.set_repeat,
                                    args=(value,)
                                ).start()

                            elif operation == "seek" and "timedelta" in request:
                                threading.Thread(
                                    target=self.seek,
                                    args=(request["timedelta"],)
                                ).start()

                            elif operation == "set_queue" and "data" in request:
                                threading.Thread(
                                    target=self.set_queue,
                                    args=(request["data"],)
                                ).start()

                            elif operation == "prepend_queue" and "data" in request:
                                threading.Thread(
                                    target=self.prepend_queue,
                                    args=(request["data"],)
                                ).start()

                            elif operation == "append_queue" and "data" in request:
                                threading.Thread(
                                    target=self.append_queue,
                                    args=(request["data"],)
                                ).start()

                            elif operation == "remove_from_queue" and "data" in request:
                                threading.Thread(
                                    target=self.remove_from_queue,
                                    args=(request["data"],)
                                ).start()

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
                time.sleep(.150)

    def _stop_server(self):
        # Stop players and threads and whatnot
        self.player.quit()

    def _build_queue(self, data):
        queue = []
        order_by_track_number = False
        artists = data.get("artist", [])
        albums = data.get("album", [])
        songs = data.get("song", [])

        if len(artists) > 0:
            order_by_track_number = True
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
            order_by_track_number = True
            for a in albums:
                try:
                    result = self.subsonic.getAlbum(a["id"])
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

    def _sort_queue(self, queue):
        try:
            ret = sorted(queue, key=itemgetter("artistId", "albumId", "discNumber", "track"))
        except:
            ret = queue
        return ret

    def _play_song(self, queue_index):
        if not self.queue:
            # Just return if there is no queue
            return False, "Can't play if there is no queue."

        if isinstance(queue_index, int) and queue_index >= 0 and queue_index < len(self.queue):
            self.current_song = queue_index
            s_id = self.queue[queue_index]["id"]
            self.player.play_song(s_id)
            return True, ""

        return False, "Index not in queue: %s" % queue_index

    def play(self, queue_index=None):
        if not self.queue:
            # No queue. Return sadness.
            return False, "Can't play if there is no queue."

        if isinstance(queue_index, int):
            return self._play_song(queue_index)

        elif self.player.is_playing():
            # Return silently if player is already playing
            return True, ""

        elif self.player.is_paused():
            # If player is paused If there is already a song playing. Press play.
            self.player.playpause()

        elif len(self.queue) > 0:
            # OK then. Nothing is playing, let's play
            # the first song in the queue.
            # self.current_song = 0
            if not self.current_song:
                self.current_song = 0
            self._play_song(self.current_song)
            return True, ""


    def play_previous_song(self):
        if self.queue and isinstance(self.current_song, int):
            queue_index = self.current_song-1
            prev_song = None
            if self.repeat and queue_index < 0:
                prev_song = len(self.queue)-1
            else:
                if queue_index >= 0:
                    prev_song = queue_index

            if isinstance(prev_song, int):
                self._play_song(prev_song)
                return True, ""

        self.stop()
        return False, "Could not play previous song."

    def play_next_song(self):
        if self.queue and isinstance(self.current_song, int):
            queue_index = self.current_song+1
            next_song = None
            if self.repeat and queue_index >= len(self.queue):
                next_song = 0
            else:
                if queue_index < len(self.queue):
                    next_song = queue_index

            if isinstance(next_song, int):
                self._play_song(next_song)
                return True, ""

        self.stop()
        return False, "Could not play next song."

    def pause(self):
        if self.player.is_playing():
            self.player.playpause()

    def playpause(self):
        self.player.playpause()

    def stop(self):
        self.player.stop()
        self.current_song = None
        if self.queue:
            self.current_song = 0

    def set_repeat(self, value):
        if not value:
            self.repeat = not self.repeat
        else:
            self.repeat = value

    def seek(self, timedelta):
        if not self.player.is_stopped():
            self.player.seek(timedelta)

    def set_queue(self, data):
        queue = self._build_queue(data)

        if "artist" in data and data["artist"] or \
                "album" in data and data["album"]:
            queue = self._sort_queue(queue)

        self.queue = queue
        self.stop()

    def prepend_queue(self, data):
        queue = self._build_queue(data)

        if "artist" in data and data["artist"] or \
                "album" in data and data["album"]:
            queue = self._sort_queue(queue)

        self.queue = queue + self.queue

        if self.queue and not self.current_song:
            self.current_song = 0

    def append_queue(self, data):
        queue = self._build_queue(data)

        if "artist" in data and data["artist"] or \
                "album" in data and data["album"]:
            queue = self._sort_queue(queue)

        self.queue += queue

        if self.queue and not self.current_song:
            self.current_song = 0

    def remove_from_queue(self, data):
        if isinstance(data, list) and len(data) == 1 and data[0] == -1:
            self.queue = []
            self.stop()
        else:
            debug("Removing from queue is not implement yet.")

    def shuffle_queue(self):
        if self.queue:
            if self.current_song:
                current_song_obj = self.queue.pop(self.current_song)

            shuffle(self.queue)

            if self.current_song:
                self.queue = [current_song_obj] + self.queue
                self.current_song = 0

    def sort_queue(self):
        if self.queue:
            if self.current_song:
                current_song_obj = self.queue[self.current_song]

            self.queue = self._sort_queue(self.queue)

            try:
                self.current_song = self.queue.index(current_song_obj)
            except:
                self.current_song = 0

    def status(self):
        if not isinstance(self.current_song, int):
            return None

        ret = {
            "song": self.queue[self.current_song],
            "player_state": self.player.player_state(),
            "progress": self.player.progress(),
            "shuffle": self.shuffle,
            "repeat": self.repeat
        }

        return ret

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
            if data.split(": ")[1] == "1":
                # EOF Code: 1 means that the song finished playing
                # by itself. Therefore we want to try to play the
                # next song in the queue.
                self.msg_queue.put("EOF")

    def _get_stream(self, song_id):
        return self.subsonic.stream(song_id)

    def progress(self):
        ret = None
        if self.mplayer.time_pos:
            try:
                ret = {
                    "percent": self.mplayer.percent_pos,
                    "time": int(self.mplayer.time_pos),
                    "length": int(self.mplayer.length),
                }
            except:
                ret = {
                    "percent": 0,
                    "time": 0,
                    "length": 0,
                }
        return ret

    def play_song(self, song_id):
        song_file = os.path.join(self.cache_dir, "%s.mp3" % song_id)

        # If not already cached. Download it.
        if not os.path.exists(song_file):
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            stream = self._get_stream(song_id)
            f = open(song_file, "wb")
            f.write(stream.read())
            f.close()

        self.mplayer.stop()
        time.sleep(0.05)
        self.mplayer.loadfile(song_file)
        time.sleep(0.05)
        self.mplayer.pause()

    def play(self):
        if self.is_paused():
            self.mplayer.pause()

    def pause(self):
        if self.is_playing():
            self.mplayer.pause()

    def playpause(self):
        self.mplayer.pause()

    def stop(self):
        self.mplayer.stop()

    def seek(self, timedelta):
        if not self.player.is_stopped() and isinstance(timedelta, int):
            time_pos = self.mplayer.time_pos
            length = self.mplayer.length
            new_time_pos = time_pos + timedelta
            if new_time_pos < 0:
                new_time_pos = 0
            elif new_time_pos > length:
                # So we have seeked passed the length of the song?
                # Play next song.
                self.msg_queue.put("EOF")

            self.mplayer.time_pos = new_time_pos

    def player_state(self):
        if self.is_playing():
            return "Playing"
        elif self.is_paused():
            return "Paused"
        else:
            return "Stopped"

    def is_playing(self):
        return bool(self.mplayer.filename and not self.mplayer.paused)

    def is_paused(self):
        return bool(self.mplayer.filename and self.mplayer.paused)

    def is_stopped(self):
        return bool(not self.mplayer.filename)

    def quit(self):
        self.mplayer.quit()

if __name__ == "__main__":
    args = docopt(__doc__, version=__version__)

    config = read_config()

    # Check if another instance of sonar-server is running.
    pidfile = os.path.join(config["sonar"]["tmp_dir"], "sonar-server.pid")
    pid = str(os.getpid())
    if os.path.isfile(pidfile):
        # Hmm, pidfile already exists. Either it is already running
        # in which case we should not start another instance of the
        # server, or the pidfile is stale (sonar-server did not exit
        # gracefully) and we should overwrite the pidfile and start
        # the server.
        pf = open(pidfile, "rt")
        existing_pid = pf.readline()
        pf.close()
        # TODO: Check if not running. In that case, go ahead.
        try:
            # Signal: 0 doesn't kill the process. Just checks if it
            # is running.
            os.kill(int(existing_pid), 0)
        except OSError:
            # If os.kill() raises OSError, we can assume that it
            # means that the process is not running. Goodie.
            pass
        else:
            # If nothing was raised, process is running. Don't
            # start another instance of the server.
            print("\nsonar-server is already running (%s)\n" % existing_pid)
            sys.exit(1)

    # Still here? Ok, write current pid and start the server.
    pf = open(pidfile, "wt")
    pf.write(pid)
    pf.close()

    # Ok, let's instantiate the server.
    server = SonarServer(msg_queue)

    try:
        # Start the server and wait for keyboard interrupt
        server._start_server()
    except KeyboardInterrupt:
        # Got keyboard interrupt. Shut down gracefully.
        print("\n\nKilled by keyboard interrupt\n")
        server._stop_server()
        try:
            # Try to remove pidfile
            os.remove(pidfile)
        except OSError:
            # The file doesn't exist. Whatever.
            pass
        sys.exit(0)

    # if "search" in args and args["search"]:
    #     client.get_search(args)
    # elif "random" in args and args["random"]:
    #     client.get_random(args)
    # elif "play" in args and args["play"]:
    #     player.play(song_id=args["SONG_ID"])
    # elif "shell" in args and args["shell"]:
    #     client.shell()
