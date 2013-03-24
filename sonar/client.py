__author__ = "Niclas Helbro <niclas.helbro@gmail.com>"

from html.parser import HTMLParser

class Client(object):
    def __init__(self, conn):
        self.conn = conn

    def _print(self, data):
        if type(data) == str:
            parser = HTMLParser()
            data = parser.unescape(data)

        print(data)

    def _print_artists(self, artists):
        if type(artists) == dict:
            artists = [artists]

        idx = 0
        for artist in artists:
            self._print("%s: %s" % (
                idx,
                artist['name']
            ))
            idx += 1

    def _print_albums(self, albums):
        if type(albums) == dict:
            albums = [albums]

        idx = 0
        for album in albums:
            self._print("%s: %s (%s)" % (
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
            self._print("%s: %s (%s)" % (
                idx,
                song['title'],
                song['artist']
            ))
            idx += 1

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
        # welcome = "Welcome to %s.\n" % __version__
        # welcome += "Written by %s\n" % __author__
        # print(welcome)

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
