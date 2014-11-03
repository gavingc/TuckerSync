"""Tucker Sync common module, common code used by server and client implementations.

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

import inspect
import json
import logging
import os


class Logger(object):

    """Custom logger wrapper.

    Typical use includes the module (file) and class name in the log output.
    By creating a module logger with the file name and adding a 'tag' to the message.

    Usage:
        # module.py:
        LOG = Logger(__file__)

        class ExampleClass(object):

            def __init__(self):
                LOG.debug(self, 'init')

            @classmethod
            def class_method(cls):
                LOG.debug(cls, 'class_method')

            @staticmethod
            def static_method():
                LOG.debug(ExampleClass, 'static_method')

        LOG.debug(None, 'Example with None tag, msg = %s', 'no tag')
        LOG.debug(msg='Example with msg = %s' % 'hello')
        LOG.debug('StringTag', 'Example with string tag and %s', 'arg')
    """

    # Internal class logger.
    _log = logging.getLogger(os.path.basename(__file__).split('.')[0] + ':Logger')
    _log.propagate = 0
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    _log.addHandler(_handler)
    # Normally set to WARN. Set to logging.DEBUG to debug this class.
    _log.setLevel(logging.WARN)

    def __init__(self, p):
        """Given a path string like __file__ (or a custom name) init a logger."""
        self._log.debug('init')
        name = os.path.basename(p).split('.')[0]
        self._log.debug('Get logger name = %s', name)
        self.logger = logging.getLogger(name)

    def get_tag(self, tag):
        """Given a tag (e.g. None, 'tag', cls, self) return None or a string.

        The returned tag string is determined from the class name or string provided.
        """
        self._log.debug('get_tag')
        if not tag:
            self._log.debug('not tag')
            return
        elif type(tag) is str:
            self._log.debug('is str')
            return tag
        elif inspect.isclass(tag):
            self._log.debug('is class')
            return tag.__name__
        else:
            self._log.debug('else object (imagine that)')
            return tag.__class__.__name__

    def debug(self, tag=None, msg='', *args, **kwargs):
        """Log at the debug level with an optional tag."""
        if not self.logger.isEnabledFor(logging.DEBUG):
            return

        t = self.get_tag(tag)

        if t:
            msg = '%s:' + msg
            args = (t,) + args

        self.logger.debug(msg, *args, **kwargs)


# Optional module logger for this module.
#LOG = Logger(__file__)


class APIQuery(object):
    """The API query constants."""

    TEST = "?type=test"
    SYNC_DOWN = "?type=syncDown"
    SYNC_UP = "?type=syncUp"


class JSONKey(object):
    """The JSON key constants."""

    ERROR = "error"
    DATA = "data"
    OBJECTS = "objects"


class APIErrorCode(object):
    """The API error code constants."""

    SUCCESS = 0
    UNKNOWN = 1
    FULL_SYNC_REQUIRED = 10


class HTTP(object):
    """HTTP constants."""

    OK = 200


class JSON(object):
    """Custom json wrapper."""

    COMPACT_SEPARATORS = (',', ':')

    @staticmethod
    def dumps(obj):
        """Dump an object to a compact json string."""
        return json.dumps(obj, separators=JSON.COMPACT_SEPARATORS)

    @staticmethod
    def loads(s):
        """Load a string and return a Python native json object."""
        return json.loads(s)

    @staticmethod
    def load(fp):
        """Load (read) a file like object and return a Python native json object."""
        return json.load(fp)
