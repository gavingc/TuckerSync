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
from common import JSON, APIErrorCode, APIErrorResponse, ResponseBody, APIRequestType
import web

urls = (
    '/', 'Index',
    '/(.*)/', 'Redirect',
    '/test/(.*)', 'Test',
    '/baseDataDown/(.*)', 'BaseDataDown',
    '/syncDown/(.*)', 'SyncDown',
    '/syncUp/(.*)', 'SyncUp',
    '/accountOpen/(.*)', 'AccountOpen',
    '/accountClose/(.*)', 'AccountClose',
    '/accountModify/(.*)', 'AccountModify'
)


class Index(object):
    """Respond to requests against application root."""

    def __init__(self):
        Log.debug(self, 'init')

    def GET(self):
        Log.debug(self, 'GET')
        return 'Welcome to Tucker Sync API.'

    def POST(self):
        Log.debug(self, 'POST')

        query = web.input(type=None)
        Log.debug(self, 'query = %s' % query)

        if query.type is None:
            return APIErrorResponse.MALFORMED_REQUEST
        if query.type == APIRequestType.TEST:
            return Test().POST()
        if query.type == APIRequestType.BASE_DATA_DOWN:
            return BaseDataDown().POST()
        if query.type == APIRequestType.SYNC_DOWN:
            return SyncDown().POST('product')
        if query.type == APIRequestType.SYNC_UP:
            return SyncUp().POST('product')
        if query.type == APIRequestType.ACCOUNT_OPEN:
            return AccountOpen().POST('product')
        if query.type == APIRequestType.ACCOUNT_CLOSE:
            return AccountClose().POST('product')
        if query.type == APIRequestType.ACCOUNT_MODIFY:
            return AccountModify().POST('product')

        # No matching request type found.
        return APIErrorResponse.MALFORMED_REQUEST


class Redirect(object):
    """Redirect (303) requests with trailing slashes."""

    def __init__(self):
        Log.debug(self, 'init')

    @staticmethod
    def GET(path):
        web.seeother('/' + path)

    @staticmethod
    def POST(path):
        web.seeother('/' + path)


class Test(object):
    """Respond to requests against /test."""

    def __init__(self):
        Log.debug(self, 'init')

    def POST(self):
        Log.debug(self, 'POST')

        query = web.input(key=None, email=None, password=None)
        Log.debug(self, 'query = %s' % query)
        return APIErrorResponse.SUCCESS


class BaseDataDown(object):
    """Base Data Download request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        objects = []

        return Packetizer.packResponse(APIErrorCode.SUCCESS, objects)


class SyncDown(object):
    """Sync Download request handler."""

    def POST(self, object_class):
        Log.debug(self, 'POST')
        Log.debug(self, 'object_class = %s' % object_class)

        with open('data.json') as f:
            jo = JSON.load(f)
            Log.debug(self, 'jo["products"][0] = %s' % jo["products"][0])

        return JSON.dumps(jo)


class SyncUp(object):
    """Sync Upload request handler."""

    def POST(self, object_class):
        Log.debug(self, 'POST')
        Log.debug(self, 'object_class = %s' % object_class)

        body = '{ "error":0, ' \
               '"objects":[{"serverObjectId":1, "lastSync":125}, {"serverObjectId":n}] }'

        return body


class AccountOpen(object):
    """Account Open request handler."""

    def POST(self, object_class):
        Log.debug(self, 'POST')
        Log.debug(self, 'object_class = %s' % object_class)

        return APIErrorResponse.SUCCESS


class AccountClose(object):
    """Account Close request handler."""

    def POST(self, object_class):
        Log.debug(self, 'POST')
        Log.debug(self, 'object_class = %s' % object_class)

        return APIErrorResponse.SUCCESS


class AccountModify(object):
    """Account Modify request handler."""

    def POST(self, object_class):
        Log.debug(self, 'POST')
        Log.debug(self, 'object_class = %s' % object_class)

        js = web.data()
        Log.debug(self, 'js = %s' % js)

        return APIErrorResponse.SUCCESS


class Log(object):
    """Custom (light) logger wrapper.

    Includes the module name and calling class name in the output.
    Lazily initialised with this module name the first time Log is called.

    Usage:
        Log.debug(self, 'value = %s' % value)
    """

    # Module logger.
    logger = logging.getLogger(__name__)
    logger.debug('Log:init.')

    @staticmethod
    def debug(obj, arg):
        Log.logger.debug('%s:%s', obj.__class__.__name__, arg)


class Packetizer(object):
    """Pack error code and any objects into a json string."""

    @staticmethod
    def packResponse(error, objects=None):
        """Pack error code and any objects into the response body. Return a json string."""
        rb = ResponseBody()
        rb.error = error
        rb.objects = objects

        # Validate before conversion.
        try:
            rb.validate()
        except Exception as e:
            Log.debug(Packetizer, 'Validate exception = %s' % e)
            return APIErrorResponse.INTERNAL_SERVER_ERROR

        try:
            js = JSON.dumps(rb.to_primitive())
        except Exception as e:
            Log.debug(Packetizer, 'JSON dumps exception = %s' % e)
            return APIErrorResponse.INTERNAL_SERVER_ERROR

        return js


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
