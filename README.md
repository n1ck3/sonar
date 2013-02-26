sonar
=====

Simple Python2 CLI for Subsonic Media Server

## Requirements

* Python >= 2.6
* py-sonic (https://github.com/crustymonkey/py-sonic)
* Subsonic Media Server (http://www.subsonic.org)

## Installation

1. Install depencendies
2. Pull this repo
3. Make sure sonar is in your path

*E.g.*
```bash
$ sudo pip install py-sonic
$ mkdir ~/src/
$ cd ~/src
$ git pull https://github.com/n1ck3/sonar
$ sudo ln -s ~/src/sonar/sonar.py /usr/bin/sonar
```

## Usage

###NOTE: This software is nowhere near useful at this point.

The following usage section acts as a implementation checklist. Any commands proceeded by a `# Not yet implemented` are...you guessed it: Not implemented yet.
___

### Searching for music

Searches return lists of 10 search results. This may be overridden with `-n int`.

*Freetext search:*
```bash
# Not yet implemented
sonar search "free text search string"
# or sonar -S "free text search string"
```

*Artist search:*
```bash
# Not yet implemented
sonar search artist "artist name"
# or sonar -sa "artist name"
```

*Album search:*
```bash
# Not yet implemented
sonar search album "album name"
# or sonar -sl "album name"
```

*Track title:*
```bash
# Not yet implemented
sonar search tracks "track title"
# or sonar -st "track title"
```

*Limit the number of results returned*
```bash
# Not yet implemented
sonar search tracks "track title" limit 10
# or sonar -st "track title" -n 0  # return all results
```

### Listing music

Listings return the full list of the listing. This may be overridden with `-n <int>`.

*List artist's albums:*
```bash
# Not yet implemented
sonar list artist "artist_ref"
# or sonar -la "artist name"  # guesses one artist
```

*List artist's tracks:*
```bash
# Not yet implemented
sonar list artist tracks "artist_ref"
# or sonar -lat "artist name"  # guesses one artist
```

*List albums's tracks:*
```bash
# Not yet implemented
sonar list album "album_ref"
# or sonar -ll "album name"  # guesses one album
```

*List playlist's tracks:*
```bash
# Not yet implemented
sonar list playlist "playlist_ref"
# or sonar -lp "playlist name"  # guesses one playlist
```

*List random albums:*
```bash
# Not yet implemented
sonar list random
# or sonar -lr
```

*Limit the number of results returned:*
```bash
# Not yet implemented
sonar -la "artist_ref" -t -n 10  # list artist tracks, limit to 10 results
sonar -la "artist_name" -t -n 0  # guesses artist name, return all results
sonar -lx -n 1  # list random albuls, limit to 1 result
```

### Playing music

Playing plays songs. Duh.

*Play artist:*
```bash
# Not yet implemented
sonar play artist "artist_ref"
# or sonar -pa  "artist name"  # guesses one artist
```

*Play albums:*
```bash
# Not yet implemented
sonar play album "album_ref"
# or sonar -pl "album name"  # huesses one album
```

*Play playlist:*
```bash
# Not yet implemented
sonar play playlist "playlist_ref"
# or sonar -pp "playlist name"  # guesses one playlist
```

### Controlling the player

Controlling the currently playing queue.

*Toggle play/pause currently playing queue:*
```bash
# Not yet implemented
sonar play
# or sonar -p
```

*Toggle play/pause currently playing queue:*
```bash
# Not yet implemented
sonar stop
# or sonar -S
```

*Play next track in currently playing queue:*
```bash
# Not yet implemented
sonar next
# or sonar -N
```

*play previous track in currently playing queue:*
```bash
# Not yet implemented
sonar previous
# or sonar prev
# or sonar -P
```

*Clear currently playing queue:*
```bash
# Not yet implemented
sonar clear
# or sonar -C
```

*Toogle shuffle currently playing queue:*
```bash
# Not yet implemented
sonar shuffle
# or sonar -X
```

*Toggle repeat currently playing queue:*
```bash
# Not yet implemented
sonar repeat
# or sonar -R
```
