#!env/bin/python

"""Tucker Sync server module.

Usage:
    See main().

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

import os
import sys
import logging
import web
from schematics.exceptions import ValidationError
import mysql.connector
from mysql.connector import errorcode
from passlib.context import CryptContext

from config import db_config
from common import JSON, APIErrorCode, APIErrorResponse, ResponseBody, APIRequestType, \
    CONTENT_TYPE_APP_JSON, User, SQLResult

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
            return AccountOpen().POST()
        if query.type == APIRequestType.ACCOUNT_CLOSE:
            return AccountClose().POST()
        if query.type == APIRequestType.ACCOUNT_MODIFY:
            return AccountModify().POST()

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

        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            return APIErrorResponse.AUTH_FAIL

        return APIErrorResponse.SUCCESS


class BaseDataDown(object):
    """Base Data Download request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        if not check_content_type():
            return APIErrorResponse.MALFORMED_REQUEST

        objects = []

        return Packetizer.packResponse(APIErrorCode.SUCCESS, objects)


class SyncDown(object):
    """Sync Download request handler."""

    def POST(self, object_class):
        Log.debug(self, 'POST')
        Log.debug(self, 'object_class = %s' % object_class)

        if not check_content_type():
            return APIErrorResponse.MALFORMED_REQUEST

        with open('data.json') as f:
            jo = JSON.load(f)
            Log.debug(self, 'jo["products"][0] = %s' % jo["products"][0])

        return JSON.dumps(jo)


class SyncUp(object):
    """Sync Upload request handler."""

    def POST(self, object_class):
        Log.debug(self, 'POST')
        Log.debug(self, 'object_class = %s' % object_class)

        if not check_content_type():
            return APIErrorResponse.MALFORMED_REQUEST

        body = '{ "error":0, ' \
               '"objects":[{"serverObjectId":1, "lastSync":125}, {"serverObjectId":n}] }'

        return body


class AccountOpen(object):
    """Account Open request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        try:
            query_user.validate()
        except ValidationError as e:
            Log.debug(self, 'Account open validation error = %s' % e)
            if 'password' in e.messages:
                return APIErrorResponse.INVALID_PASSWORD
            elif 'email' in e.messages:
                return APIErrorResponse.INVALID_EMAIL
            else:
                return APIErrorResponse.INTERNAL_SERVER_ERROR

        # Hash password before database insertion.
        query_user.password = password_context().encrypt(query_user.password)

        statement = User.INSERT
        params = query_user.insert_params()

        sql_result = execute_statement(statement, params, User, False)

        Log.debug(self, 'sql_result = %s' % sql_result.to_native())

        if sql_result.errno == errorcode.ER_DUP_ENTRY:
            return APIErrorResponse.EMAIL_NOT_UNIQUE
        elif sql_result.errno:
            return APIErrorResponse.INTERNAL_SERVER_ERROR

        return APIErrorResponse.SUCCESS


class AccountClose(object):
    """Account Close request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            return APIErrorResponse.AUTH_FAIL

        statement = User.DELETE
        params = query_user.delete_params()

        sql_result = execute_statement(statement, params, User, False)

        Log.debug(self, 'sql_result = %s' % sql_result.to_native())

        if sql_result.errno:
            return APIErrorResponse.INTERNAL_SERVER_ERROR

        return APIErrorResponse.SUCCESS


class AccountModify(object):
    """Account Modify request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        if not check_content_type():
            return APIErrorResponse.MALFORMED_REQUEST

        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            return APIErrorResponse.AUTH_FAIL

        js = web.data()
        Log.debug(self, 'js = %s' % js)

        try:
            jo = JSON.loads(js)
        except Exception as e:
            Log.logger.debug('JSON loads exception = %s' % e)
            return APIErrorResponse.INVALID_JSON_OBJECT

        new_user = User()
        new_user.email = jo.get('email')
        new_user.password = jo.get('password')

        try:
            new_user.validate()
        except ValidationError as e:
            Log.debug(self, 'Account open validation error = %s' % e)
            if 'password' in e.messages:
                return APIErrorResponse.INVALID_PASSWORD
            elif 'email' in e.messages:
                return APIErrorResponse.INVALID_EMAIL
            else:
                return APIErrorResponse.INTERNAL_SERVER_ERROR

        # Hash password before database insertion.
        new_user.password = password_context().encrypt(new_user.password)

        statement = User.UPDATE_BY_EMAIL
        params = new_user.update_by_email_params(query_user.email)

        sql_result = execute_statement(statement, params, User, False)

        Log.debug(self, 'sql_result = %s' % sql_result.to_native())

        if sql_result.errno == errorcode.ER_DUP_ENTRY:
            return APIErrorResponse.EMAIL_NOT_UNIQUE
        elif sql_result.errno:
            return APIErrorResponse.INTERNAL_SERVER_ERROR

        return APIErrorResponse.SUCCESS


class Log(object):
    """Custom (light) logger wrapper.

    Includes the module (file) name and calling class name in the output.
    Lazily initialised with this module (file) name the first time Log is called.

    Usage:
        Log.debug(self, 'value = %s' % value)
        Log.logger.debug('Accessing logger directly.')
    """

    # Module logger.
    logger = logging.getLogger(os.path.basename(__file__).split('.')[0])
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


def execute_statement(statement, params, object_class, is_select=True):
    """Execute the provided SQL statement taking care of opening and closing the connection.

    :param statement: String SQL statement to execute.
    :param params: Tuple of params to apply to statement, must match.
    :param object_class: Model class to fill the result objects list with (SELECT only).
    :param is_select: Boolean default True, MUST be set to False for Data Manipulation Statements (
    INSERT/DELETE/UPDATE/CREATE)
    :return: SQLResult
    """
    sql_result = SQLResult()

    try:
        cnx = mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        Log.logger.debug('MySQL error no = %s' % e.errno)
        Log.logger.debug('MySQL error msg = %s' % e.msg)
        sql_result.errno = e.errno
        return sql_result

    try:
        cursor = cnx.cursor(dictionary=True)
    except mysql.connector.Error as e:
        Log.logger.debug('MySQL error no = %s' % e.errno)
        Log.logger.debug('MySQL error msg = %s' % e.msg)
        sql_result.errno = e.errno
        _close_db(None, cnx)
        return sql_result

    try:
        cursor.execute(statement, params)
    except mysql.connector.Error as e:
        Log.logger.debug('MySQL error no = %s' % e.errno)
        Log.logger.debug('MySQL error msg = %s' % e.msg)
        sql_result.errno = e.errno
        _close_db(cursor, cnx)
        return sql_result

    if is_select:
        for row in cursor:
            Log.logger.debug('row = %s' % row)
            try:
                instance = object_class(row)
            except Exception as e:
                Log.logger.debug('Instance creation exception = %s' % e)
                break
            try:
                instance.validate()
            except Exception as e:
                Log.logger.debug('Instance validate exception = %s' % e)
                break
            sql_result.objects.append(instance)
    else:
        cnx.commit()  # Commit after a sequence of DML statements.

    sql_result.rowcount = cursor.rowcount
    sql_result.lastrowid = cursor.lastrowid

    _close_db(cursor, cnx)

    return sql_result


def _close_db(cursor, cnx):
    """Close the cursor and connection."""
    try:
        cursor.close()
    except Exception as e:
        Log.logger.debug('Cursor close exception = %s' % e)

    try:
        cnx.close()
    except Exception as e:
        Log.logger.debug('Connection close exception = %s' % e)


def check_content_type():
    """Content-Type check returns True if Content-Type is correct, False otherwise."""

    Log.logger.debug('check_content_type')

    content_type = web.ctx.env.get('CONTENT_TYPE')
    Log.logger.debug('Content-Type = %s' % content_type)

    if content_type == CONTENT_TYPE_APP_JSON:
        return True
    else:
        Log.logger.debug('Check Fail, Content-Type != %s' % CONTENT_TYPE_APP_JSON)
        return False


def check_auth(user):
    """Check authorisation.
    :param user: User to check authorisation against existing account on server.
    :return: True if authorised, False otherwise.
    """

    Log.logger.debug('check_auth')

    try:
        user.validate()
    except ValidationError as e:
        Log.logger.debug('Check auth user validation error = %s' % e)
        return False

    statement = User.SELECT_BY_EMAIL
    params = user.select_by_email_params()

    sql_result = execute_statement(statement, params, User)

    Log.logger.debug('sql_result = %s' % sql_result.to_native())

    if sql_result.errno:
        return False

    if sql_result.objects:
        ret_user = sql_result.objects[0]
        Log.logger.debug('email = %s' % ret_user.email)
        Log.logger.debug('password = %s' % ret_user.password)
        if password_context().verify(user.password, ret_user.password):
            return True

    return False


password_context_holder = None


def password_context():
    """Create the password context on demand.
    :return: CryptContext
    """
    global password_context_holder

    if password_context_holder:
        return password_context_holder

    password_context_holder = CryptContext(
        # Supported schemes.
        schemes=["sha256_crypt"],
        default="sha256_crypt",

        # Vary rounds parameter randomly when creating new hashes.
        all__vary_rounds=0.1,

        # Set a good starting point for rounds selection
        sha512_crypt__min_rounds=60000,
        sha256_crypt__min_rounds=80000,

        # If the admin user category is selected, make a much stronger hash,
        admin__sha512_crypt__min_rounds=120000,
        admin__sha256_crypt__min_rounds=160000)

    return password_context_holder


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
