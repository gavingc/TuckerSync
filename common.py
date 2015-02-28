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
from schematics.types import StringType, IntType, BaseType, LongType, EmailType, UUIDType, \
    URLType, BooleanType
from schematics.types.compound import ListType, ModelType
from schematics.transforms import whitelist

from config import USER_PASSWORD_MIN_LEN


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
    CLIENT_UUID_NOT_UNIQUE = 9
    FULL_SYNC_REQUIRED = 10

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
    CLIENT_UUID_NOT_UNIQUE = '{"%s":%s}' % (JSONKey.ERROR, APIErrorCode.CLIENT_UUID_NOT_UNIQUE)
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


class APIRequest(Model):
    """API Request Model."""

    base_url = URLType()
    type = StringType()
    key = StringType()
    email = StringType()
    password = StringType()

    user_agent = StringType(serialized_name='User-Agent', default='TuckerSync')
    accept = StringType(serialized_name='Accept', default=CONTENT_TYPE_APP_JSON)
    content_type = StringType(serialized_name='Content-Type', default=CONTENT_TYPE_APP_JSON)

    body = StringType()

    class Options(object):
        roles = {'params': whitelist('type', 'key', 'email', 'password'),
                 'base_headers': whitelist('user_agent'),
                 'accept_headers': whitelist('user_agent', 'accept'),
                 'content_headers': whitelist('user_agent', 'accept', 'content_type')}

    @property
    def params(self):
        return self.to_native(role='params')

    @property
    def headers(self):
        if self.body:
            return self.to_native(role='content_headers')
        else:
            return self.to_native(role='accept_headers')

    @property
    def base_headers(self):
        return self.to_native(role='base_headers')


class SyncDownRequestBody(Model):
    """Sync download request body model."""

    objectClass = StringType(required=True)
    clientUUID = UUIDType(required=True)
    lastSync = LongType(required=True)


class BaseDataDownRequestBody(SyncDownRequestBody):
    """Base data download request body model."""

    pass


class SyncUpRequestBody(Model):
    """Sync upload request body model."""

    objectClass = StringType(required=True)
    clientUUID = UUIDType(required=True)
    objects = ListType(ModelType(Model), required=True)


class AccountOpenRequestBody(Model):
    """Account open request body model."""

    clientUUID = UUIDType(required=True)


class AccountModifyRequestBody(Model):
    """Account modify request body model."""

    email = StringType(required=True)
    password = StringType(required=True)


class ResponseBody(Model):
    """Response body model."""

    error = IntType(default=0)
    objects = BaseType(serialize_when_none=False)


class SQLResult(Model):
    """SQL results and errors."""

    errno = IntType()
    err_msg = StringType()
    rowcount = LongType()
    lastrowid = LongType()
    objects = ListType(ModelType(Model), default=[])


class SyncCount(Model):
    """SyncCount is a core application database model."""

    sync_count = LongType()
    object_class = StringType()
    is_committed = BooleanType()

    # Select committed sync count by object class.
    # Operation:
    # Select the uncommitted sessions for object class and return the lowest syncCount - 1,
    # otherwise if no uncommitted sessions return the highest sync count for object class,
    # otherwise if no records return 0.
    SELECT_COMMITTED_SC = """SELECT
            CASE WHEN COUNT(*) THEN MIN(syncCount) - 1
            ELSE (SELECT
                    CASE WHEN COUNT(*) THEN MAX(syncCount)
                    ELSE 0
                    END
                 FROM SyncCount
                 WHERE objectClass = %s)
            END AS sync_count
        FROM SyncCount
        WHERE objectClass = %s
              AND isCommitted = 0"""

    def select_committed_sc_params(self):
        return self.object_class, self.object_class

    # Insert uncommitted session for object class.
    INSERT = """INSERT INTO SyncCount (objectClass) VALUES (%s)"""

    def insert_params(self):
        return self.object_class,

    # Delete committed sessions prior to the currently inserted one.
    # Dependant on LAST_INSERT_ID() of the current database connection.
    DELETE_TRAILING_COMMITTED = """DELETE
        FROM SyncCount
        WHERE syncCount < LAST_INSERT_ID()
            AND objectClass = %s
            AND isCommitted = 1"""

    def delete_trailing_committed_params(self):
        return self.object_class,

    # Select session sync count by object class.
    # Putting the sequence together to issue a session sync count.
    # Must be executed outside of the main data transaction.
    # Operation:
    # First a new uncommitted session is inserted.
    # This becomes the new sync count head marker (not committed_sc).
    # Then trailing committed sessions are deleted to keep the table size small.
    # Some rows are locked during the delete but insert with auto_increment will still function
    #  for parallel sessions.
    # The session sync count is returned from LAST_INSERT_ID() which is within the current database
    # connection and does not read from the table.
    SELECT_SESSION_SC = (INSERT,
                         'COMMIT',
                         DELETE_TRAILING_COMMITTED,
                         'COMMIT',
                         'SELECT LAST_INSERT_ID() AS sync_count')

    def select_session_sc_params(self):
        return (self.insert_params(),
                None,
                self.delete_trailing_committed_params(),
                None,
                None)

    # Mark session sync count as committed.
    # Marking the session committed must be atomic with the data commit.
    # However the session must still be marked as committed after a data transaction fail/rollback.
    # Therefore should initially be executed within the same connection and transaction as the
    # data and again if the data transaction fails.
    UPDATE_SET_IS_COMMITTED = """UPDATE SyncCount SET isCommitted = 1 WHERE syncCount = %s"""

    def update_set_is_committed_params(self):
        return self.sync_count,

    # Mark expired past and future sessions as committed.
    # Provides self healing from any rare cases of sessions that failed to be marked as committed.
    # Configured expiry time is 1 hour 20 min.
    # Which should allow sessions at least 20 min to commit even in the case of daylight savings
    # being applied to server (although the UTC to local time zone may handle this effectively).
    # The normal case of time jitter and drift/update should be handled by the expiry time.
    # The committed rows will be deleted when the next session sync count is issued.
    # If any rows are affected a warning should be logged:
    WARN_EXPIRED_SESSIONS_COMMITTED = 'There were uncommitted sessions over 1 hour 20 min in the' \
                                      ' past or future! These expired sessions (%s) have been' \
                                      ' marked as committed.'

    UPDATE_SET_IS_COMMITTED_EXPIRED = """UPDATE SyncCount
        SET isCommitted = 1
        WHERE objectClass = %s
          AND isCommitted = 0
          AND (createAt < SUBTIME(NOW(),'01:20:00')
              OR createAt > ADDTIME(NOW(),'01:20:00'))"""

    def update_set_is_committed_expired_params(self):
        return self.object_class,


class Client(Model):
    """Client is a core application database model."""

    rowid = LongType()
    userId = LongType()
    UUID = UUIDType(serialized_name='clientUUID', required=True)

    SELECT_BY_UUID = """SELECT id as rowid, userId, UUID FROM Client WHERE UUID = %s"""

    def select_by_uuid_params(self):
        return self.uuid,

    INSERT = """INSERT INTO Client (userId, UUID) VALUES (%s, %s)"""

    def insert_params(self):
        return self.userId, str(self.UUID)

    INSERT_BY_LAST_INSERT_ID = """INSERT INTO Client (userId, UUID) VALUES (LAST_INSERT_ID(), %s)"""

    def insert_by_last_insert_id_params(self):
        return str(self.UUID),


class User(Model):
    """User is a core application database model."""

    rowid = LongType()
    email = EmailType(required=True)
    password = StringType(min_length=USER_PASSWORD_MIN_LEN, required=True)
    clients = ListType(ModelType(Client), default=[])

    SELECT_BY_EMAIL = """SELECT id as rowid, email, password FROM User WHERE email = %s"""

    def select_by_email_params(self):
        return self.email,

    INSERT = """INSERT INTO User (email, password) VALUES (%s, %s)"""

    def insert_params(self):
        return self.email, self.password

    UPDATE_BY_EMAIL = """UPDATE User SET email = %s, password = %s  WHERE email = %s"""

    def update_by_email_params(self, where_email):
        return self.email, self.password, where_email

    DELETE = """DELETE FROM User WHERE email = %s"""

    def delete_params(self):
        return self.email,


class UserClient(User):
    """User Client join model."""

    client_rowid = LongType()
    UUID = UUIDType()

    SELECT_BY_EMAIL = """SELECT u.id AS rowid, u.email, u.password, c.id AS client_rowid, c.UUID
                          FROM User AS u
                          LEFT JOIN Client AS c ON c.userId = u.id
                          WHERE u.email = %s
                          LIMIT 100"""

    def select_by_email_params(self):
        return self.email,
