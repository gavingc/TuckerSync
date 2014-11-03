#!env/bin/python

"""Tucker Sync server module.

Usage:
    See main().

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

import sys
import logging
from common import JSON
import web

urls = (
    '/', 'Index',
    '/(.*)/', 'Redirect',
    '/test', 'Test',
    '/syncDown/(.*)', 'SyncDown',
    '/syncUp/(.*)', 'SyncUp'
)


class Index(object):
    """Respond to requests against application root."""

    def __init__(self):
        Log.debug(self, 'init')

    def GET(self):
        Log.debug(self, 'GET')

        query = web.input(type=None)
        Log.debug(self, 'query = %s' % query)

        if query.type == 'test':
            return Test().GET()
        if query.type == 'syncDown':
            return SyncDown().GET('product')
        if query.type == 'syncUp':
            return SyncUp().GET('product')
        else:
            return 'Welcome to Tucker Sync API'


class Redirect(object):
    """Redirect (303) requests with trailing slashes."""

    def __init__(self):
        Log.debug(self, 'init')

    @staticmethod
    def GET(path):
        web.seeother('/' + path)


class Test(object):
    """Respond to requests against /test."""

    def __init__(self):
        Log.debug(self, 'init')

    def GET(self):
        Log.debug(self, 'GET')

        query = web.input(email=None, password=None)
        Log.debug(self, 'query = %s' % query)
        return '{"error":0}'


class SyncDown(object):
    """Sync Download Phase API handler."""

    def GET(self, object_class):
        Log.debug(self, 'GET')
        Log.debug(self, 'object_class = %s' % object_class)

        with open('data.json') as f:
            jo = JSON.load(f)
            Log.debug(self, 'jo["products"][0] = %s' % jo["products"][0])

        return JSON.dumps(jo)


class SyncUp(object):
    """Sync Upload Phase API handler."""

    def GET(self, object_class):
        Log.debug(self, 'GET')
        Log.debug(self, 'object_class = %s' % object_class)

        body = '{ "error":0, ' \
               '"objects":[{"serverObjectId":1, "lastSync":125}, {"serverObjectId":n}] }'

        return body


class Log(object):
    """Custom (light) logger wrapper.

    Includes the module name and calling class name in the output.
    Lazily initialised with the module name the first time Log is called.

    Usage:
        Log.debug(self, 'value = %s' % value)
    """

    # Module logger.
    logger = logging.getLogger(__name__)
    logger.debug('Log:init.')

    @staticmethod
    def debug(obj, arg):
        Log.logger.debug('%s:%s', obj.__class__.__name__, arg)


def main():
    """Run the server.

    May be run from the command line or as a CGI script.

    Usage:
        ./server.py
    """

    app = web.application(urls, globals())
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    app.run()


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main()
