sonar
=====

Simple Python3 CLI for Subsonic Media Server

## Requirements

* Python3
* docopt (https://github.com/docopt/docopt)
* MPlayer (http://www.mplayerhq.hu)
* mplayer.py (https://github.com/baudm/mplayer.py.git)
* Subsonic Media Server (http://www.subsonic.org)
* py-sonic (https://github.com/n1ck3/py-sonic) (Note: master-py3 banch)

## Installation

1. Install depencendies
2. Pull this repo
3. Make sure either you have all the deps in your [python] path or link them into the sonar repo.
4. Copy and edit the `sonar.conf` file to your home directory `~/sonar.conf`.
5. Make sure sonar is in your path for easier usage:

*E.g.*
After having installed and configured `Subsonc` and `MPlayer`:
```bash
$ mkdir ~/src && cd ~/src
$ git pull https://github.com/docopt/docopt
$ mplayer.py (https://github.com/baudm/mplayer.py.git)
$ git pull https://github.com/n1ck3/py-sonic && cd py-sonic && git checkout master-py3 && cd ..
$ git pull https://github.com/n1ck3/sonar
$ cd sonar && ln -s ../docopt . && ln -s ../mplayer.py/mplayer . && ln -s ../py-sonic/libsonic . && cd ..
$ sudo ln -s ~/src/sonar/sonar.py /usr/bin/sonar
```

## Usage
### NOTE: This software is nowhere near useful at this point.

This assumes that you have pulled this repo into `~/src/sonar`

### Sonar Server
At this point, you have to run the server in it's own terminal window (sure you can fork it and whatnot, but you are going to know whats going on with the server as it is likely to crash at any point in time. :))

```
Usage:
    sonarserver.py
```

### Sonar Client
```
Usage:
    sonar.py search [(artist|album|song) SEARCH_STRING...] [--limit LIMIT]
    sonar.py random [album|song] [--limit LIMIT]
    sonar.py last
    sonar.py play [INDEX...]
    sonar.py pause
    sonar.py (playpause|pp)
    sonar.py stop
    sonar.py next
    sonar.py (ff|rw) [TIMEDELTA]
    sonar.py queue [show|clear|[[set|prepend|append] INDEX...]]
    sonar.py status [--short]
    sonar.py
```

## Cool features
* Search for artist, albums, or songs.
* Listing random albums or songs.
* Limiting returned results at will.
* Queue songs on server.
* Play queue (using mplayer).
* Pause player.
* Play/Pause toggle.
* Stop player.
* Seek forward backward in currently playing song (with optional timedelta argument).
* Showing player status (verbose or short)
* Songs are cached for fast playback.

## Known issues
* I had to fork the py-sonic (master-py3 branch) and run 2to3 (and tweak a few things) in order to make it play nice with python3. This does however not work properly. At this point, only searching and queueing songs works as expected.
* ~~Playing next song in the queue doesn't work.~~ [FIXED]
* ~~I don't know if seeking (ff, rw) works properly.~~ [PARTIALLY FIXED]. rw to a time_pos < 0 sets it to the beginning of song. ff to time_pos > song.length sets it to song.length-1 for now.
* Coninuous play (the player plays the next song in the queue on finished playing a song).
* Handle errors from server in client better. I.e. is server can't play queue index, let the user know.

## Roadmap
* ~~Being able to skip to the next song in the queue.~~ [FIXED]
* Threading all the server calls in order to return quickly in the client.
* ~~Better server queue handling (keep queue but knowing which song is being played and thus being able to skip forward and backward in the queue.~~ [FIXED]
* Add ability to remove songs from server queue.
* Better (proper) logging for both the server and client. That is, cleaning up the stdout output to a minimum (ability to change that with --debug or --verbose) but writing to logs for trouble shooting.
* Lazy starting of the server if not running when wanting to use it with the client.
* Ability to list and queue playlists (and further down the road creating and deleting playlists as well as adding songs to and remove songs from playlists).
* Implementing Subsonic Jukebox (ability to play music on the subsonic server rather than the client -- play the music on the good speakers at home).
* Limiting song cache size in mb (server will automatically remove songs that were touched the longest time ago when the limit is reached).

## Long term roadmap
* Fixing py-sonic for python3 and pull requesting it to crustymonkey.
