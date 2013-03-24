__author__ = "Niclas Helbro <niclas.helbro@gmail.com>"

import threading

class Player(object):
    def __init__(self, conn):
        self.conn = conn

    def get_stream(self, song_id):
        return self.conn.stream(song_id)

    def play(self):
        pass

    def stop(self):
        # if not self.current_list:
            # return

        # self.current_list.stop()
        # self.current_list.join()
        pass

class PlayerThread(threading.Thread):
    def __init__(self, player, song_id):
        self.player = player
        self.song_id = song_id

        self._stop = threading.Event()

        super(PlayerThread, self).__init__()

    def run(self):
        stream = self.player.get_stream(self.song_id)

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
