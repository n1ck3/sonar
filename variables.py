#!/usr/bin/env python3

import os

# Directories
HOME_DIR = os.path.expanduser('~')
CONFIG_DIR = "%s/.config/sonar" % HOME_DIR
CACHE_DIR = "%s/.cache/sonar" % HOME_DIR
MUSIC_CACHE_DIR = "%s/music_cache" % CACHE_DIR
LOG_DIR = "%s/.local/logs/sonar" % HOME_DIR
RUN_DIR = "%s/.local/run/sonar" % HOME_DIR

# Files
PID_FILE = "%s/sonar-server.pid" % RUN_DIR
CONFIG_FILE = "%s/sonar.conf" % CONFIG_DIR
SERVER_LOG_FILE = "%s/sonar-server.log" % LOG_DIR
CLIENT_LOG_FILE = "%s/sonar-client.log" % LOG_DIR

# Log config
LOG_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'server-console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            # 'level': 'INFO',
            'stream': 'ext://sys.stdout'
        },
        'server-file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            # 'level': 'INFO',
            'filename': SERVER_LOG_FILE,
            'maxBytes': 1024000,
            'backupCount': 3
        },
        'client-console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            # 'level': 'WARNING',
            'stream': 'ext://sys.stdout'
        },
        'client-file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            # 'level': 'INFO',
            'filename': CLIENT_LOG_FILE,
            'maxBytes': 1024000,
            'backupCount': 3
        }
    },
    'loggers': {
        'sonar-server': {
            'handlers': ['server-console', 'server-file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'sonar-client': {
            'handlers': ['client-console', 'client-file'],
            'level': 'WARNING',
            'propagate': True
        },
    }
}
