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
$ git clone https://github.com/docopt/docopt
$ git clone https://github.com/baudm/mplayer.py.git)
$ git clone https://github.com/n1ck3/py-sonic && cd py-sonic && git checkout master-py3 && cd ..
$ git clone https://github.com/n1ck3/sonar
$ cd sonar && ln -s ../docopt/docopt.py . && ln -s ../mplayer.py/mplayer . && ln -s ../py-sonic/libsonic . && cd ..
$ sudo ln -s ~/src/sonar/sonar.py /usr/bin/sonar && sudo ln -s ~/src/sonar/sonar-server.py /usr/bin/sonar-server
```

## Usage
### NOTE: This software is not ready yet. However, it does have the fundamental functionality present and working.

This assumes that you followed the instructions above which had you link the python scripts to a folder that is in you $PATH as `sonar` and `sonar-server`.

### Sonar Server
At this point, you have to run the server in it's own terminal window (sure you can fork it and whatnot, but you are going to know whats going on with the server as it is likely to crash at any point in time. :))

```
Usage:
    sonar-server.py
```

### Sonar Client
```
Usage:
    sonar.py search [(artist|album|song) SEARCH_STRING...] [--limit LIMIT]
    sonar.py random [album|song] [--limit LIMIT]
    sonar.py (last|list)
    sonar.py play [INDEX]
    sonar.py pause
    sonar.py (playpause|pp)
    sonar.py stop
    sonar.py (prev|next)
    sonar.py (rw|ff) [TIMEDELTA]
    sonar.py repeat [on|off]
    sonar.py queue [show|shuffle|[[set|(prepend|first)|(append|add|last)|(remove|clear)] INDEX...]]
    sonar.py [status] [--short]
```

## Cool features
* Search for artist, albums, or songs.
* Listing random albums or songs.
* Limiting returned results at will.
* Queue songs on server.
* Play queue.
* Clear queue.
* Shuffle queue.
* Pause player.
* Play/Pause toggle.
* Stop player.
* Seek forward backward in currently playing song (with optional timedelta argument).
* Showing player status (verbose or short)
* Songs are cached for fast playback.

## ~~Known issues~~ Check out the issues
* I had to fork the py-sonic (master-py3 branch) and run 2to3 (and tweak a few things) in order to make it play nice with python3. This does however not work properly. At this point, only searching and queueing songs works as expected.

## Roadmap
* Add ability to remove songs from server queue. [Issue #1]
* Better (proper) logging for both the server and client. That is, cleaning up the stdout output to a minimum (ability to change that with --debug or --verbose) but writing to logs for trouble shooting. [Issue #4]
* Lazy starting of the server if not running when wanting to use it with the client. [Issue #5]
* Ability to list and queue playlists (and further down the road creating and deleting playlists as well as adding songs to and remove songs from playlists). [Issue #15]
* Ability to handle playlists (adding songs to and remove songs from playlists). [Issue #16]
* Implementing Subsonic Jukebox (ability to play music on the subsonic server rather than the client -- play the music on the good speakers at home). [Issue #9]
* Limiting song cache size in mb (server will automatically remove songs that were touched the longest time ago when the limit is reached). [Issue #10]
* Handle errors from server in client better. I.e. is server can't play queue index, let the user know. [Issue #8]

## Long term roadmap
* Fixing py-sonic for python3 and pull requesting it to crustymonkey. [Issue #11]
