#!/usr/bin/env python3

import os
import sys
import traceback
import configparser
from urllib.error import HTTPError

from pysonic.libsonic.connection import Connection

from variables import CONFIG_DIR, CACHE_DIR, MUSIC_CACHE_DIR, LOG_DIR, RUN_DIR
from variables import CONFIG_FILE

def ensure_paths():
    for path in [CONFIG_DIR, CACHE_DIR, MUSIC_CACHE_DIR, LOG_DIR, RUN_DIR]:
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

def read_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    try:
        if not os.path.exists(CONFIG_FILE):
            raise OSError

        # Valiadate media-server section
        assert "media-server" in config
        assert "host" in config["media-server"]
        assert "port" in config["media-server"]
        assert "user" in config["media-server"]
        assert "password" in config["media-server"]

        # Valiadate sonar-server section
        assert "sonar" in config
        assert "host" in config["sonar"]
        assert "port" in config["sonar"]

        try:
            assert isinstance(config.getboolean("sonar", "prefetch"), bool)
        except ValueError:
            raise AssertionError

        assert "cache_limit" in config["sonar"]
        try:
            assert isinstance(config.getint("sonar", "cache_limit"), int)
        except ValueError:
            raise AssertionError

    except OSError:
        print("\nNo config file found.\n")
        print("Copy and modify `sonar.conf` to `%s`\n" % CONFIG_FILE)
        sys.exit(1)
    except AssertionError as e:
        _,_,tb = sys.exc_info()
        #traceback.print_tb(tb)
        tbInfo = traceback.extract_tb(tb)
        filename,line,func,text = tbInfo[-1]
        print("\nMalformed config file.\n")
        print("Please fix: %s \n" % text)
        sys.exit(1)

    return config


class Subsonic():
    def __init__(self):
        self.config = read_config()
        self.connection = self.connect()

    def connect(self):
        connection = Connection(
            self.config["media-server"]["host"],
            self.config["media-server"]["user"],
            self.config["media-server"]["password"],
            port=self.config["media-server"]["port"]
        )
        try:
            connection.getLicense()
        except HTTPError as e:
            print(e)
            print("\nCould not connect to server.")
            print("\nMake sure your confs are good.\n")
            sys.exit(0)

        return connection
