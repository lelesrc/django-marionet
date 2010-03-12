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


# Logging class
class Log:
    """Logging class, with five severity levels.
    """
    # Increasing levels of severity
    _levels = {
        'debug': 1,
        'info': 2,
        'warning': 3,
        'error': 4,
        'critical': 5}

    def __init__(self, level='info'):
        """Create a logger with the given severity level."""
        self.setlevel(level)

    def setlevel(self,level):
        self.level = level

    def message(self, level, text):
        """Print a message if it's at the current severity level or higher."""
        if Log._levels[level] >= Log._levels[self.level]:
            print(text)

    def debug(self, text):
        """Log a debugging message."""
        self.message('debug', text)

    def info(self, text):
        """Log an informational message."""
        self.message('info', text)

    def warning(self, text):
        """Log a warning message."""
        self.message('warning', "WARNING: " + text)

    def error(self, text):
        """Log an error message."""
        self.message('error', "ERROR: " + text)

    def critical(self, text):
        """Log a critical error message."""
        self.message('critical', "CRITICAL: " + text)



# Global logger
log = Log()
