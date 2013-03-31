import os
import sys
import datetime
import configparser
import json
from urllib.error import HTTPError

import libsonic

def pretty(data, indent=2):
    print(
        json.dumps(
            (data),
            sort_keys=True,
            indent=indent
        )
    )

def debug(data):
    date_string = datetime.datetime.now().strftime("%H:%M:%S")
    if isinstance(data, str):
        print("[debug %s] %s" % (date_string, data))
    else:
        print("[debug %s] %s" % (
            date_string,
            json.dumps((data), sort_keys=True)
        ))


def read_config():
    config_file = "%s/.sonar.conf" % os.path.expanduser('~')
    config = configparser.ConfigParser()
    config.read(config_file)
    try:
        if not os.path.exists(config_file):
            raise OSError

        # Valiadate server section
        assert "sonar" in config
        assert "tmp_dir" in config["sonar"]

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

class Subsonic(object):
    def __init__(self):
        self.config = read_config()
        self.connection = self.connect()

    def connect(self):
        connection = libsonic.Connection(
            self.config["subsonic"]["host"],
            self.config["subsonic"]["user"],
            self.config["subsonic"]["password"],
            port=self.config["subsonic"]["port"]
        )
        try:
            connection.getLicense()
        except HTTPError:
            print("\nCould not connect to server.")
            print("\nMake sure your confs are good.\n")
            sys.exit(0)

        return connection
