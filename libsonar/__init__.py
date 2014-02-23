import os
import sys
import configparser
import json
from urllib.error import HTTPError

from pysonic.libsonic.connection import Connection


def read_config():
    config_file = "%s/.sonar.conf" % os.path.expanduser('~')
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        if not os.path.exists(config_file):
            raise OSError

        # Valiadate server section
        assert "sonar" in config
        assert "sonar_dir" in config["sonar"]
        assert "prefetch_next_song" in config["sonar"]

        # Valiadate server section
        assert "server" in config
        assert "host" in config["server"]
        assert "port" in config["server"]

        # Valiadate subsonic section
        assert "subsonic" in config
        assert "host" in config["subsonic"]
        assert "port" in config["subsonic"]
        assert "user" in config["subsonic"]
        assert "password" in config["subsonic"]
    except OSError:
        print("\nNo config file found.\n")
        print("Copy and modify `sonar.conf` to `~/.sonar.conf`\n")
        sys.exit(0)
    except AssertionError:
        print("\nMalformed config file.\n")
        print("Copy and modify `sonar.conf` to `~/.sonar.conf`\n")
        sys.exit(0)

    return config


class Subsonic():
    def __init__(self):
        self.config = read_config()
        self.connection = self.connect()

    def connect(self):
        connection = Connection(
            self.config["subsonic"]["host"],
            self.config["subsonic"]["user"],
            self.config["subsonic"]["password"],
            port=self.config["subsonic"]["port"]
        )
        try:
            connection.getLicense()
        except HTTPError as e:
            print(e)
            print("\nCould not connect to server.")
            print("\nMake sure your confs are good.\n")
            sys.exit(0)

        return connection
