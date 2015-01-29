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
import logging
import web
from schematics.exceptions import ValidationError
import mysql.connector
from mysql.connector import errorcode
from passlib.context import CryptContext

from config import db_config, APP_KEYS, PRODUCTION, LOG_FILE_NAME, LOG_LEVEL
from common import JSON, APIErrorCode, APIErrorResponse, ResponseBody, APIRequestType, \
    CONTENT_TYPE_APP_JSON, User, Client, SQLResult, BaseDataDownRequestBody, \
    SyncDownRequestBody, AccountOpenRequestBody, SyncUpRequestBody, AccountModifyRequestBody

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
        Log.debug(self, 'response = Welcome to Tucker Sync API.')
        return 'Welcome to Tucker Sync API.'

    def POST(self):
        Log.debug(self, 'POST')

        query = web.input(type=None)

        ## Request Type ##
        if query.type is None:
            Log.debug(self, 'query type is None.')
            Log.debug(self, 'response = malformed request.')
            return APIErrorResponse.MALFORMED_REQUEST
        if query.type == APIRequestType.TEST:
            return Test().POST()
        if query.type == APIRequestType.BASE_DATA_DOWN:
            return BaseDataDown().POST()
        if query.type == APIRequestType.SYNC_DOWN:
            return SyncDown().POST()
        if query.type == APIRequestType.SYNC_UP:
            return SyncUp().POST()
        if query.type == APIRequestType.ACCOUNT_OPEN:
            return AccountOpen().POST()
        if query.type == APIRequestType.ACCOUNT_CLOSE:
            return AccountClose().POST()
        if query.type == APIRequestType.ACCOUNT_MODIFY:
            return AccountModify().POST()

        Log.debug(self, 'request type match not found.')
        Log.debug(self, 'response = malformed request.')
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

        ## Auth Check ##
        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            Log.debug(self, 'response = auth fail')
            return APIErrorResponse.AUTH_FAIL

        Log.debug(self, 'response = success')
        return APIErrorResponse.SUCCESS


class BaseDataDown(object):
    """Base Data Download request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        ## Auth Check Not Required ##

        ## Request Body ##
        request_body, error_response = get_request_body(BaseDataDownRequestBody)

        if error_response:
            return error_response

        objects = []

        return Packetizer.packResponse(APIErrorCode.SUCCESS, objects)


class SyncDown(object):
    """Sync Download request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        ## Auth Check ##
        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            Log.debug(self, 'response = auth fail')
            return APIErrorResponse.AUTH_FAIL

        ## Request Body ##
        request_body, error_response = get_request_body(SyncDownRequestBody)

        if error_response:
            return error_response

        objects = []

        return Packetizer.packResponse(APIErrorCode.SUCCESS, objects)


class SyncUp(object):
    """Sync Upload request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        ## Auth Check ##
        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            Log.debug(self, 'response = auth fail')
            return APIErrorResponse.AUTH_FAIL

        ## Request Body ##
        request_body, error_response = get_request_body(SyncUpRequestBody)

        if error_response:
            return error_response

        objects = []

        return Packetizer.packResponse(APIErrorCode.SUCCESS, objects)


class AccountOpen(object):
    """Account Open request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        ## New User ##
        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        try:
            query_user.validate()
        except ValidationError as e:
            Log.debug(self, 'query_user validation error = %s' % e)
            if 'password' in e.messages:
                Log.debug(self, 'response = invalid password')
                return APIErrorResponse.INVALID_PASSWORD
            elif 'email' in e.messages:
                Log.debug(self, 'response = invalid email')
                return APIErrorResponse.INVALID_EMAIL
            else:
                Log.debug(self, 'response = internal server error')
                return APIErrorResponse.INTERNAL_SERVER_ERROR

        # Hash password before database insertion.
        query_user.password = password_context().encrypt(query_user.password)

        ## Request Body ##
        request_body, error_response = get_request_body(AccountOpenRequestBody)

        if error_response:
            return error_response

        ## New Client ##
        client = Client()
        client.UUID = request_body.clientUUID

        ## Execute Inserts ##
        statements = (User.INSERT, Client.INSERT_BY_LAST_INSERT_ID)
        params = (query_user.insert_params(), client.insert_by_last_insert_id_params())

        sql_result = execute_statements(statements, params, User, False)

        error_response = handle_user_sql_result_error(sql_result)

        if error_response:
            return error_response

        Log.debug(self, 'response = success')
        return APIErrorResponse.SUCCESS


class AccountClose(object):
    """Account Close request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        ## Auth Check ##
        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            Log.debug(self, 'response = auth fail')
            return APIErrorResponse.AUTH_FAIL

        ## Execute Delete ##
        statement = User.DELETE
        params = query_user.delete_params()

        sql_result = execute_statement(statement, params, User, False)

        error_response = handle_user_sql_result_error(sql_result)

        if error_response:
            return error_response

        Log.debug(self, 'response = success')
        return APIErrorResponse.SUCCESS


class AccountModify(object):
    """Account Modify request handler."""

    def POST(self):
        Log.debug(self, 'POST')

        ## Auth Check ##
        query = web.input(email=None, password=None)

        query_user = User()
        query_user.email = query.email
        query_user.password = query.password

        if not check_auth(query_user):
            Log.debug(self, 'response = auth fail')
            return APIErrorResponse.AUTH_FAIL

        ## Request Body ##
        request_body, error_response = get_request_body(AccountModifyRequestBody)

        if error_response:
            return error_response

        new_user = User()
        new_user.email = request_body.email
        new_user.password = request_body.password

        try:
            new_user.validate()
        except ValidationError as e:
            Log.debug(self, 'new_user validation error = %s' % e)
            if 'password' in e.messages:
                Log.debug(self, 'response = invalid password')
                return APIErrorResponse.INVALID_PASSWORD
            elif 'email' in e.messages:
                Log.debug(self, 'response = invalid email')
                return APIErrorResponse.INVALID_EMAIL
            else:
                Log.debug(self, 'response = internal server error')
                return APIErrorResponse.INTERNAL_SERVER_ERROR

        # Hash password before database insertion.
        new_user.password = password_context().encrypt(new_user.password)

        Log.debug(self, 'new_user.email = %s' % new_user.email)
        Log.debug(self, 'new_user.password = %s' % new_user.password)

        ## Execute Update ##
        statement = User.UPDATE_BY_EMAIL
        params = new_user.update_by_email_params(query_user.email)

        sql_result = execute_statement(statement, params, User, False)

        error_response = handle_user_sql_result_error(sql_result)

        if error_response:
            return error_response

        Log.debug(self, 'response = success')
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
    logger.debug('Log:init')

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
            Log.debug(Packetizer, 'response body validation exception = %s' % e)
            Log.debug(Packetizer, 'response = internal server error')
            return APIErrorResponse.INTERNAL_SERVER_ERROR

        try:
            js = JSON.dumps(rb.to_primitive())
        except Exception as e:
            Log.debug(Packetizer, 'JSON dumps exception = %s' % e)
            Log.debug(Packetizer, 'response = internal server error')
            return APIErrorResponse.INTERNAL_SERVER_ERROR

        Log.debug(Packetizer, 'response = success + objects')
        return js


def execute_statement(statement, params, object_class, is_select=True):
    """Convenience wrapper for execute_statements. Wraps single statement and params in tuples."""
    return execute_statements((statement,), (params,), object_class, is_select)


def execute_statements(statements, params, object_class, is_select=True):
    """Execute the provided SQL statements taking care of opening and closing the db connection.

    :param tuple[str] statements: SQL statements to execute.
    :param tuple[tuple[str]] params: params to apply to statements.
    :param object_class: schematics.models.Model class to populate results list with.
    :param bool is_select: MUST be set to False for Data Manipulation Statements (
    INSERT/DELETE/UPDATE/CREATE).
    :rtype: SQLResult
    """
    Log.logger.debug('execute_statement')
    Log.logger.debug('statements = %s', statements)
    Log.logger.debug('params = %s', params)

    sql_result = SQLResult()

    cursor, cnx, sql_result.errno = _open_db()

    if sql_result.errno:
        return sql_result

    try:
        for i, stmt in enumerate(statements):
            cursor.execute(stmt, params[i])
        if not is_select:
            cnx.commit()  # Commit after a sequence of DML statements.
    except mysql.connector.Error as e:
        Log.logger.debug('MySQL error no = %s', e.errno)
        Log.logger.debug('MySQL error msg = %s', e.msg)
        sql_result.errno = e.errno
        sql_result.err_msg = e.msg
        _close_db(cursor, cnx)
        return sql_result

    if is_select:
        for row in cursor:
            try:
                instance = object_class(row)
            except Exception as e:
                Log.logger.debug('instance creation exception = %s', e)
                break
            try:
                instance.validate()
            except Exception as e:
                Log.logger.debug('instance validation exception = %s', e)
                break
            sql_result.objects.append(instance)

    sql_result.rowcount = cursor.rowcount
    sql_result.lastrowid = cursor.lastrowid

    _close_db(cursor, cnx)

    return sql_result


def handle_user_sql_result_error(sql_result):
    """Handle the sql_result errors, if any, from a User insert or update.

    :param SQLResult sql_result: instance of results to handle.
    :return: error_response if any, otherwise None.
    """
    Log.logger.debug('sql_result = %s' % sql_result.to_native())

    if sql_result.errno == errorcode.ER_DUP_ENTRY:
        if "for key 'email'" in sql_result.err_msg:
            Log.logger.debug('response = email not unique')
            return APIErrorResponse.EMAIL_NOT_UNIQUE
        elif "for key 'UUID'" in sql_result.err_msg:
            Log.logger.debug('response = client uuid not unique')
            return APIErrorResponse.CLIENT_UUID_NOT_UNIQUE
        else:
            Log.logger.debug('response = internal server error')
            return APIErrorResponse.INTERNAL_SERVER_ERROR

    elif sql_result.errno:
        Log.logger.debug('response = internal server error')
        return APIErrorResponse.INTERNAL_SERVER_ERROR


def _open_db():
    """Open the connection and cursor. Return cursor, cnx, errno."""
    try:
        cnx = mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        Log.logger.debug('MySQL error no = %s', e.errno)
        Log.logger.debug('MySQL error msg = %s', e.msg)
        return None, None, e.errno

    try:
        cursor = cnx.cursor(dictionary=True)
    except mysql.connector.Error as e:
        Log.logger.debug('MySQL error no = %s', e.errno)
        Log.logger.debug('MySQL error msg = %s', e.msg)
        _close_db(None, cnx)
        return None, None, e.errno

    return cursor, cnx, None


def _close_db(cursor, cnx):
    """Close the cursor and connection."""
    try:
        cursor.close()
    except Exception as e:
        Log.logger.debug('cursor close exception = %s', e)

    try:
        cnx.close()
    except Exception as e:
        Log.logger.debug('connection close exception = %s', e)


def get_request_body(model_class):
    """Get the request body as a model instance. Return request_body and error_response."""

    ## Get json object (Python Dictionary) from request body. ##
    jo, error_response = get_json_object()

    if error_response:
        return None, error_response

    try:
        request_body = model_class(jo)  # strict=True; jo must have exact keys.
    except Exception as e:
        Log.logger.debug('instance creation exception = %s', e)
        Log.logger.debug('response = invalid json object')
        return None, APIErrorResponse.INVALID_JSON_OBJECT

    try:
        request_body.validate()
    except ValidationError as e:
        Log.logger.debug('request_body validation error = %s', e)
        Log.logger.debug('response = invalid json object')
        return None, APIErrorResponse.INVALID_JSON_OBJECT

    return request_body, None


def get_json_object():
    """Get the json object (Python dictionary) from the request. Return jo and error_response."""

    if not check_content_type():
        Log.logger.debug('response = malformed request')
        return None, APIErrorResponse.MALFORMED_REQUEST

    js = web.data()
    if not PRODUCTION:
        Log.logger.debug('js = %s' % js)

    try:
        jo = JSON.loads(js)
    except Exception as e:
        Log.logger.debug('JSON loads exception = %s', e)
        Log.logger.debug('response = invalid json object')
        return None, APIErrorResponse.INVALID_JSON_OBJECT

    if not type(jo) is dict:
        Log.logger.debug('type of jo is not an object/dict.')
        Log.logger.debug('response = invalid json object')
        return None, APIErrorResponse.INVALID_JSON_OBJECT

    if not PRODUCTION:
        Log.logger.debug('jo = %s' % jo)

    # Success.
    return jo, None


def check_content_type():
    """Content-Type check returns True if Content-Type is correct, False otherwise."""

    Log.logger.debug('check_content_type')

    content_type = web.ctx.env.get('CONTENT_TYPE')
    Log.logger.debug('Content-Type = %s', content_type)

    if content_type == CONTENT_TYPE_APP_JSON:
        return True
    else:
        Log.logger.debug('Check Fail, Content-Type != %s', CONTENT_TYPE_APP_JSON)
        return False


def check_auth(user):
    """Check authorisation.

    :param User user: to check authorisation against existing account on server.
    :return: True if authorised, False otherwise.
    """

    Log.logger.debug('check_auth')

    try:
        user.validate()
    except ValidationError as e:
        Log.logger.debug('user validation error = %s', e)
        return False

    statement = User.SELECT_BY_EMAIL
    params = user.select_by_email_params()

    sql_result = execute_statement(statement, params, User)

    Log.logger.debug('sql_result = %s', sql_result.to_native())

    if sql_result.errno:
        return False

    if sql_result.objects:
        ret_user = sql_result.objects[0]
        Log.logger.debug('ret_user.email = %s', ret_user.email)
        Log.logger.debug('ret_user.password = %s', ret_user.password)
        if password_context().verify(user.password, ret_user.password):
            return True

    return False


password_context_holder = None


def password_context():
    """Create the password context on demand.

    :rtype: CryptContext
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


def begin_request_processor(handle):
    """Begin request processor."""
    Log.logger.debug('------------------------------------------------------')
    Log.logger.debug('begin_request_processor')

    query = web.input(type=None, key=None, email=None, password=None)

    Log.logger.debug('query.type = %s', query.type)
    Log.logger.debug('query.key = %s', query.key)
    Log.logger.debug('query.email = %s', query.email)

    if not PRODUCTION:
        Log.logger.debug('query.password = %s', query.password)

    if web.ctx.method == 'GET':
        # App key not required.
        return handle()

    ## Key Check ##
    if query.key is None:
        Log.logger.debug('query key is None')
        Log.logger.debug('response = malformed request')
        return APIErrorResponse.MALFORMED_REQUEST

    if query.key not in APP_KEYS:
        Log.logger.debug('response = invalid key')
        return APIErrorResponse.INVALID_KEY

    return handle()


def main():
    """Run the server.

    May be run from the command line or as a CGI script.

    Usage:
        ./server.py
    """

    # Get log level from config.
    log_level = getattr(logging, LOG_LEVEL.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('invalid log level: %s' % LOG_LEVEL)

    if PRODUCTION:
        from logging.handlers import RotatingFileHandler
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=300000, backupCount=1)
        root_logger.addHandler(handler)
    else:
        from sys import stderr
        logging.basicConfig(stream=stderr, level=log_level)

    app = web.application(urls, globals())
    app.add_processor(begin_request_processor)
    app.run()


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main()
