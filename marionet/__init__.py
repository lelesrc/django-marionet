# -*- coding: utf-8 -*-

import os

# Python < 3.x
try:
    from ConfigParser import ConfigParser
# Python 3.x
except ImportError:
    from configparser import ConfigParser

# Configuration file reader/writer
class Config (ConfigParser):
    """Interface for reading/writing marionet configuration files. Just a wrapper
    around the standard library ConfigParser.

    See the ConfigParser documentation for details.
    """
    # Dictionary of suite-wide configuration defaults
    DEFAULTS = {
        'work_dir': '/tmp',
	}

    def __init__(self):
        """Load configuration."""
        ConfigParser.__init__(self, self.DEFAULTS)

