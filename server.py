#!/usr/bin/env python
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Steven Tucker and Gavin Kromhout
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import json
import sys
import logging
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
            j1 = json.load(f)
            Log.debug(self, 'j1["products"][0] = %s' % j1["products"][0])

        return json.dumps(j1)


class SyncUp(object):
    """Sync Upload Phase API handler."""

    def GET(self, object_class):
        Log.debug(self, 'GET')
        Log.debug(self, 'object_class = %s' % object_class)

        body = '{ "error":0, ' \
               '"objects":[{"serverObjectId":1, "lastSync":125}, {"serverObjectId":n}] }'

        return body


class Log(object):
    """Custom logger wrapper.

    Use: Log.debug(self, 'value = %s' % value)Includes the calling
    class name in the output.
    """

    # Module logger.
    logger = logging.getLogger(__name__)
    logger.debug('Log init.')

    @staticmethod
    def debug(obj, arg):
        Log.logger.debug('%s:%s', obj.__class__.__name__, arg)


def main():
    """Called when this module is the primary one."""

    app = web.application(urls, globals())
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    app.run()


if __name__ == "__main__":
    # Run main when commands read either from standard input,
    # from a script file, or from an interactive prompt.
    main()
