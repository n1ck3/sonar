sonar
=====

Simple Python3 CLI for Subsonic Media Server

## System dependencies

* Python3
* MPlayer (http://www.mplayerhq.hu)
* Subsonic Media Server (http://www.subsonic.org)

## Submodules
* docopt (https://github.com/docopt/docopt)
* py-sonic (https://github.com/crustymonkey/py-sonic@python3)
* mplayer.py (https://github.com/baudm/mplayer.py.git)

## Installation

1. Install system depencendies
1. Pull this repo
1. Initialize and update all submodules
1. Copy and edit the `sonar.conf` file to your home directory `~/sonar.conf`.
1. Make sure sonar and sonar-server is in your path for easier usage.
   Optionally alias them to something short that you don't mind writing a lot.
   ;)

**Example setup blow-by-blow**
After having installed and configured `Subsonc` and `MPlayer`:
```bash
$ mkdir -p ~/git ; cd ~/git
$ git clone https://github.com/n1ck3/sonar
$ cd sonar
$ git submodule init && git submodule update
$ sudo ln -s sonar.py /usr/bin/sonar
$ sudo ln -s sonar-server.py /usr/bin/sonar-server
```

## Usage
### NOTE: This software is not ready yet. However, it does have the fundamental functionality present and working.

This assumes that you followed the instructions above which had you link the python scripts to a folder that is in you $PATH as `sonar` and `sonar-server`.

### Sonar Server
At this point, you have to run the server in it's own terminal window (sure you can fork it and whatnot, but you are going to know whats going on with the server as it is likely to crash at any point in time. :))

```
Usage:
    sonar-server.py [options]

Options:
    -h --help                   Shows this screen
    -l --loglevel LOGLEVEL      Set the loglevel [default: info]
                                (critical | error | warning | info | debug)
    --version                   Show version
```

### Sonar Client
```
Usage:
    sonar.py search [artist | album | song] (SEARCH_STRING...) [options]
    sonar.py playlists [options]
    sonar.py cached [options]
    sonar.py random [album | song] [options]
    sonar.py last [options]
    sonar.py play [INDEX...] [options]
    sonar.py pause [options]
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
```

## Cool features
* Search for artist, albums, or songs
* List your playlists **(New)**
* List your cached (downloaded) songs **(New)**
* List random albums or songs
* Limiting returned results at will
* Queue songs on server
* Play queue
* Clear queue
* Shuffle / sort queue
* Play/Pause player
* Stop player
* Seek forward backward in currently playing song (with optional timedelta argument).
* Showing player status (verbose, short, or json (appropriate for statusbars))
* Cache the so you don't have to download it again next time you want to listen to dat Bieber tune.
* Prefetch next song in queue for fast playback **(New)**

## Roadmap
* Add ability to remove songs from server queue. [Issue #1]
* Lazy starting of the server if not running when wanting to use it with the client. [Issue #5]
* Ability to handle playlists (adding songs to and remove songs from playlists). [Issue #16]
* Implementing Subsonic Jukebox (ability to play music on the subsonic server rather than the client -- play the music on the good speakers at home). [Issue #9]
* Handle errors from server in client better. I.e. is server can't play queue index, let the user know. [Issue #8]
