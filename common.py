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
from schematics.models import Model
from schematics.types import StringType, IntType, BaseType, LongType, EmailType, UUIDType
from schematics.types.compound import ListType, ModelType

from config import USER_PASSWORD_LEN


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


class APIRequestType(object):
    """The API request constants."""

    TEST = 'test'
    BASE_DATA_DOWN = 'baseDataDown'
    SYNC_DOWN = 'syncDown'
    SYNC_UP = 'syncUp'
    ACCOUNT_OPEN = 'accountOpen'
    ACCOUNT_CLOSE = 'accountClose'
    ACCOUNT_MODIFY = 'accountModify'


class JSONKey(object):
    """The JSON key constants."""

    ERROR = 'error'
    DATA = 'data'
    OBJECTS = 'objects'


class APIErrorCode(object):
    """The API error code constants."""

    SUCCESS = 0
    INTERNAL_SERVER_ERROR = 1
    MALFORMED_REQUEST = 2
    INVALID_KEY = 3
    INVALID_EMAIL = 4
    INVALID_PASSWORD = 5
    AUTH_FAIL = 6
    INVALID_JSON_OBJECT = 7
    EMAIL_NOT_UNIQUE = 8
    FULL_SYNC_REQUIRED = 9

    @classmethod
    def name(cls, error_code):
        """Lazy reverse lookup, returns the first name that matches error_code."""
        for k, v in cls.__dict__.items():
            if v == error_code:
                return k


class APIErrorResponse(object):
    """The API error response constants."""

    SUCCESS = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.SUCCESS)
    INTERNAL_SERVER_ERROR = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.INTERNAL_SERVER_ERROR)
    MALFORMED_REQUEST = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.MALFORMED_REQUEST)
    INVALID_KEY = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.INVALID_KEY)
    INVALID_EMAIL = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.INVALID_EMAIL)
    INVALID_PASSWORD = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.INVALID_PASSWORD)
    AUTH_FAIL = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.AUTH_FAIL)
    INVALID_JSON_OBJECT = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.INVALID_JSON_OBJECT)
    EMAIL_NOT_UNIQUE = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.EMAIL_NOT_UNIQUE)
    FULL_SYNC_REQUIRED = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.FULL_SYNC_REQUIRED)


class HTTP(object):
    """HTTP constants."""

    OK = 200


CONTENT_TYPE_APP_JSON = 'application/json'


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


class APIURL(Model):
    """API URL Model."""

    URL_FORMAT = '%(base_url)s' \
                 '?type=%(type)s' \
                 '&key=%(key)s' \
                 '&email=%(email)s' \
                 '&password=%(password)s'

    base_url = StringType()
    type = StringType()
    key = StringType()
    email = StringType()
    password = StringType()

    def url_string(self):
        return APIURL.URL_FORMAT % self.to_native()


class SyncDownRequestBody(Model):
    """Sync download request body model."""

    objectClass = StringType()
    clientUUID = StringType()
    lastSync = LongType(default=0)


class BaseDataDownRequestBody(SyncDownRequestBody):
    """Base data download request body model."""

    pass


class SyncUpRequestBody(Model):
    """Sync upload request body model."""

    objectClass = StringType()
    clientUUID = StringType()
    objects = BaseType(serialize_when_none=False)


class AccountModifyRequestBody(Model):
    """Account modify request body model."""

    email = StringType()
    password = StringType()


class ResponseBody(Model):
    """Response body model."""

    error = IntType(default=0)
    objects = BaseType(serialize_when_none=False)


class SQLResult(Model):
    """SQL results and errors."""

    errno = IntType()
    rowcount = LongType()
    lastrowid = LongType()
    objects = ListType(ModelType(Model), default=[])


class User(Model):
    """User is a core application model class."""

    rowid = LongType()
    email = EmailType(required=True)
    password = StringType(min_length=USER_PASSWORD_LEN, required=True)

    SELECT_BY_EMAIL = """SELECT id as rowid, email, password FROM User WHERE email = %s"""

    def select_by_email_params(self):
        return self.email,

    INSERT = """INSERT INTO User (email, password) VALUES (%s,%s)"""

    def insert_params(self):
        return self.email, self.password

    UPDATE_BY_EMAIL = """UPDATE User SET email = %s, password = %s  WHERE email = %s"""

    def update_by_email_params(self, where_email):
        return self.email, self.password, where_email

    DELETE = """DELETE FROM User WHERE email = %s"""

    def delete_params(self):
        return self.email,


class Client(Model):
    """Client is a core application model class."""

    rowid = LongType()
    UUID = UUIDType(required=True)
    UserID = LongType()
