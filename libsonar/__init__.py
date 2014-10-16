import os
import sys
import traceback
import configparser
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
        try:
            assert isinstance(config.getboolean("sonar", "prefetching"), bool)
        except ValueError:
            raise AssertionError
        assert "cache_limit" in config["sonar"]
        try:
            assert isinstance(config.getint("sonar", "cache_limit"), int)
        except ValueError:
            raise AssertionError

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
