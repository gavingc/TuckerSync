#!env/bin/python

"""Tucker Sync server module.

Implemented with Werkzeug Python WSGI Utility Library.

Usage:
    Launch from CGI script (see index.py and .htaccess):
        #!env/bin/python

        from flup.server.cgi import WSGIServer
        from server import application

        WSGIServer(application).run()

    Run development server from the command line:
        ./server.py

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

import logging
from os.path import basename
import mysql.connector
from mysql.connector import errorcode
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.wrappers import BaseRequest, CommonRequestDescriptorsMixin, \
    BaseResponse, CommonResponseDescriptorsMixin
from schematics.exceptions import ValidationError
from passlib.context import CryptContext

from app_config import LOG_FILE_NAME, LOG_LEVEL, PRODUCTION, APP_KEYS, db_config
from common import CONTENT_TYPE_APP_JSON, APIErrorResponse, APIRequestType, UserClient, User, \
    SQLResult, Client, JSON, AccountOpenRequestBody, SyncDownRequestBody, ResponseBody, \
    APIErrorCode, SyncUpRequestBody, AccountModifyRequestBody, BaseDataDownRequestBody


def logging_init():
    """Init logging with app_config settings."""

    # Get log level from config.
    log_level = getattr(logging, LOG_LEVEL.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('invalid log level: %s' % LOG_LEVEL)

    if PRODUCTION:
        from logging.handlers import RotatingFileHandler

        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=300000, backupCount=1)
        formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
    else:
        from sys import stderr

        logging.basicConfig(stream=stderr, level=log_level)

# Module logger.
logging_init()
log = logging.getLogger(basename(__file__).split('.')[0])


class Request(BaseRequest, CommonRequestDescriptorsMixin):
    pass


class Response(BaseResponse, CommonResponseDescriptorsMixin):
    pass


class Holder(object):
    """Holder of the current request resources."""

    def __init__(self):
        self.cnx = None
        self.cursor = None
        self.password_context = None


def open_db():
    """Open the connection and cursor. Return cursor, cnx, errno."""
    db_config['raise_on_warnings'] = True

    try:
        cnx = mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        log.debug('MySQL error no = %s', e.errno)
        log.debug('MySQL error msg = %s', e.msg)
        return None, None, e.errno

    try:
        cursor = cnx.cursor(dictionary=True)
    except mysql.connector.Error as e:
        log.debug('MySQL error no = %s', e.errno)
        log.debug('MySQL error msg = %s', e.msg)
        # noinspection PyTypeChecker
        close_db(None, cnx)
        return None, None, e.errno

    return cursor, cnx, None


def close_db(cursor, cnx):
    """Close the cursor and connection."""
    try:
        cursor.close()
    except Exception as e:
        log.debug('cursor close exception = %s', e)

    try:
        cnx.close()
    except Exception as e:
        log.debug('connection close exception = %s', e)


def execute_statement(statement, params, object_class, holder=None, is_select=True):
    """Convenience wrapper for execute_statements. Wraps single statement and params in tuples."""
    return execute_statements((statement,), (params,), object_class, holder, is_select)


def execute_statements(statements, params, object_class, holder=None, is_select=True):
    """Execute the provided SQL statements.

    :param tuple[str] statements: SQL statements to execute.
    :param tuple[tuple[str]] params: params to apply to statements.
    :param object_class: schematics.models.Model class to populate results list with.
    :param Holder holder: provides the database cnx and cursor. If none a connection is open/closed.
    :param bool is_select: MUST be set to False for Data Manipulation Statements (
    INSERT/DELETE/UPDATE/CREATE).
    :rtype: SQLResult
    """
    log.debug('execute_statements()')
    log.debug('statements = %s', statements)
    log.debug('params = %s', params)

    sql_result = SQLResult()

    if holder:
        cursor = holder.cursor
        cnx = holder.cnx
    else:
        cursor, cnx, sql_result.errno = open_db()
        if sql_result.errno:
            return sql_result

    try:
        for i, stmt in enumerate(statements):
            cursor.execute(stmt, params[i])
        if not is_select:
            cnx.commit()  # Commit after a sequence of DML statements.
    except mysql.connector.Error as e:
        log.debug('MySQL error no = %s', e.errno)
        log.debug('MySQL error msg = %s', e.msg)
        sql_result.errno = e.errno
        sql_result.err_msg = e.msg
        if not holder:
            close_db(cursor, cnx)
        return sql_result

    if is_select:
        for row in cursor:
            try:
                instance = object_class(row)
            except Exception as e:
                log.debug('instance creation exception = %s', e)
                break
            try:
                instance.validate()
            except Exception as e:
                log.debug('instance validation exception = %s', e)
                break
            sql_result.objects.append(instance)

    sql_result.rowcount = cursor.rowcount
    sql_result.lastrowid = cursor.lastrowid

    if not holder:
        close_db(cursor, cnx)

    return sql_result


def handle_user_sql_result_error(sql_result):
    """Handle the sql_result errors, if any, from a User insert or update.

    :param SQLResult sql_result: instance of results to handle.
    :return: error_response if any, otherwise None.
    """
    log.debug('sql_result = %s' % sql_result.to_native())

    if sql_result.errno == errorcode.ER_DUP_ENTRY:
        if "for key 'email'" in sql_result.err_msg:
            log.debug('response = email not unique')
            return APIErrorResponse.EMAIL_NOT_UNIQUE
        elif "for key 'UUID'" in sql_result.err_msg:
            log.debug('response = client uuid not unique')
            return APIErrorResponse.CLIENT_UUID_NOT_UNIQUE
        else:
            log.debug('response = internal server error')
            return APIErrorResponse.INTERNAL_SERVER_ERROR

    elif sql_result.errno:
        log.debug('response = internal server error')
        return APIErrorResponse.INTERNAL_SERVER_ERROR


def application_key_fails(request, response):
    """Private application key check. Return True if the check fails."""

    query_key = request.args.get('key')

    if query_key is None:
        log.debug('query key is None')
        log.debug('response = malformed request')
        response.set_data(APIErrorResponse.MALFORMED_REQUEST)
        return True

    if query_key not in APP_KEYS:
        log.debug('response = invalid key')
        response.set_data(APIErrorResponse.INVALID_KEY)
        return True


def content_type_fails(request, response):
    """Content-Type check. Return True if the check fails."""

    if request.content_type != CONTENT_TYPE_APP_JSON:
        log.debug('Content-Type = %s', request.content_type)
        log.debug('Check Fail, Content-Type != %s', CONTENT_TYPE_APP_JSON)
        response.set_data(APIErrorResponse.MALFORMED_REQUEST)
        return True


def get_json_object(request, response):
    """Get the json object (Python dictionary) from the request.

    Return jo, otherwise None."""

    if content_type_fails(request, response):
        return

    js = request.get_data()
    if not PRODUCTION:
        log.debug('js = %s' % js)

    try:
        jo = JSON.loads(js)
    except Exception as e:
        log.debug('JSON loads exception = %s', e)
        log.debug('response = invalid json object')
        response.set_data(APIErrorResponse.INVALID_JSON_OBJECT)
        return

    if not type(jo) is dict:
        log.debug('type of jo is not an object/dict.')
        log.debug('response = invalid json object')
        response.set_data(APIErrorResponse.INVALID_JSON_OBJECT)
        return

    if not PRODUCTION:
        log.debug('jo = %s' % jo)

    # Success.
    return jo


def get_request_body(request, response, model_class):
    """Get the request body as a model instance.

    Return request_body, otherwise None."""

    jo = get_json_object(request, response)

    if not jo:
        return

    try:
        request_body = model_class(jo)  # strict=True; jo must have exact keys.
    except Exception as e:
        log.debug('instance creation exception = %s', e)
        log.debug('response = invalid json object')
        response.set_data(APIErrorResponse.INVALID_JSON_OBJECT)
        return

    try:
        request_body.validate()
    except ValidationError as e:
        log.debug('request_body validation error = %s', e)
        log.debug('response = invalid json object')
        response.set_data(APIErrorResponse.INVALID_JSON_OBJECT)
        return

    return request_body


def pack_response(response, error, objects=None):
    """Pack error code and any objects into the response body."""

    rb = ResponseBody()
    rb.error = error
    rb.objects = objects

    # Validate before conversion.
    try:
        rb.validate()
    except Exception as e:
        log.debug('response body validation exception = %s' % e)
        log.debug('response = internal server error')
        response.set_data(APIErrorResponse.INTERNAL_SERVER_ERROR)
        return

    try:
        js = JSON.dumps(rb.to_primitive())
    except Exception as e:
        log.debug('JSON dumps exception = %s' % e)
        log.debug('response = internal server error')
        response.set_data(APIErrorResponse.INTERNAL_SERVER_ERROR)
        return

    log.debug('response = success + objects')
    response.set_data(js)


def password_context(holder):
    """Create the password context on demand.

    :type holder: Holder
    :rtype: CryptContext
    """

    if holder.password_context:
        return holder.password_context

    holder.password_context = CryptContext(
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

    return holder.password_context


def get_authenticated_user(request, response, holder):
    """Get authenticated user from database. Return auth_user, otherwise None."""

    log.debug('get_authenticated_user()')

    query_user = UserClient()
    query_user.email = request.args.get('email')
    query_user.password = request.args.get('password')

    try:
        query_user.validate()
    except ValidationError as e:
        log.debug('query_user validation error = %s', e)
        log.debug('response = auth fail')
        response.set_data(APIErrorResponse.AUTH_FAIL)
        return

    sql_result = execute_statement(
        statement=UserClient.SELECT_BY_EMAIL,
        params=query_user.select_by_email_params(),
        object_class=UserClient,
        holder=holder)

    log.debug('sql_result = %s', sql_result.to_native())

    if sql_result.errno:
        log.debug('response = internal server error')
        response.set_data(APIErrorResponse.INTERNAL_SERVER_ERROR)
        return

    if not sql_result.objects:
        log.debug('response = auth fail')
        response.set_data(APIErrorResponse.AUTH_FAIL)
        return

    user_client = sql_result.objects[0]

    auth_user = User()
    auth_user.rowid = user_client.rowid
    auth_user.email = user_client.email
    auth_user.password = user_client.password

    log.debug('auth_user.email = %s', auth_user.email)
    log.debug('auth_user.password = %s', auth_user.password)

    if not password_context(holder).verify(query_user.password, auth_user.password):
        log.debug('response = auth fail')
        response.set_data(APIErrorResponse.AUTH_FAIL)
        return

    # Append Clients #
    for uc in sql_result.objects:
        client = Client()
        client.rowid = uc.client_rowid
        client.UUID = uc.UUID
        auth_user.clients.append(client)

    # Success.
    log.debug('user authenticated')
    return auth_user


def test(request, response, holder):
    """Test request handler."""

    log.debug('test()')

    auth_user = get_authenticated_user(request, response, holder)
    if not auth_user:
        return

    log.debug('response = success')
    response.set_data(APIErrorResponse.SUCCESS)


def base_data_down(request, response, holder):
    """Base Data Download request handler."""

    log.debug('base_data_down()')

    # Auth Check Not Required #

    request_body = get_request_body(request,
                                    response,
                                    BaseDataDownRequestBody)
    if not request_body:
        return

    objects = []

    pack_response(response, APIErrorCode.SUCCESS, objects)


def sync_down(request, response, holder):
    """Sync Download request handler."""

    log.debug('sync_down()')

    auth_user = get_authenticated_user(request, response, holder)
    if not auth_user:
        return

    request_body = get_request_body(request,
                                    response,
                                    SyncDownRequestBody)
    if not request_body:
        return

    objects = []

    pack_response(response, APIErrorCode.SUCCESS, objects)


def sync_up(request, response, holder):
    """Sync Upload request handler."""

    log.debug('sync_up()')

    auth_user = get_authenticated_user(request, response, holder)
    if not auth_user:
        return

    request_body = get_request_body(request,
                                    response,
                                    SyncUpRequestBody)
    if not request_body:
        return

    objects = []

    pack_response(response, APIErrorCode.SUCCESS, objects)


def account_open(request, response, holder):
    """Account Open request handler."""

    log.debug('account_open()')

    new_user = User()
    new_user.email = request.args.get('email')
    new_user.password = request.args.get('password')

    try:
        new_user.validate()
    except ValidationError as e:
        log.debug('new_user validation error = %s' % e)
        if 'password' in e.messages:
            log.debug('response = invalid password')
            response.set_data(APIErrorResponse.INVALID_PASSWORD)
            return
        elif 'email' in e.messages:
            log.debug('response = invalid email')
            response.set_data(APIErrorResponse.INVALID_EMAIL)
            return
        else:
            log.debug('response = internal server error')
            response.set_data(APIErrorResponse.INTERNAL_SERVER_ERROR)
            return

    # Hash password before database insertion.
    new_user.password = password_context(holder).encrypt(new_user.password)

    request_body = get_request_body(request,
                                    response,
                                    AccountOpenRequestBody)
    if not request_body:
        return

    new_client = Client()
    new_client.UUID = request_body.clientUUID

    sql_result = execute_statements(
        statements=(User.INSERT,
                    Client.INSERT_BY_LAST_INSERT_ID),
        params=(new_user.insert_params(),
                new_client.insert_by_last_insert_id_params()),
        object_class=User,
        holder=holder,
        is_select=False)

    error_response = handle_user_sql_result_error(sql_result)

    if error_response:
        response.set_data(error_response)
        return

    log.debug('response = success')
    response.set_data(APIErrorResponse.SUCCESS)


def account_close(request, response, holder):
    """Account Close request handler."""

    log.debug('account_close()')

    auth_user = get_authenticated_user(request, response, holder)
    if not auth_user:
        return

    sql_result = execute_statement(
        statement=User.DELETE,
        params=auth_user.delete_params(),
        object_class=User,
        holder=holder,
        is_select=False)

    error_response = handle_user_sql_result_error(sql_result)

    if error_response:
        response.set_data(error_response)
        return

    log.debug('response = success')
    response.set_data(APIErrorResponse.SUCCESS)


def account_modify(request, response, holder):
    """Account Modify request handler."""

    log.debug('account_modify()')

    auth_user = get_authenticated_user(request, response, holder)
    if not auth_user:
        return

    request_body = get_request_body(request,
                                    response,
                                    AccountModifyRequestBody)
    if not request_body:
        return

    mod_user = User()
    mod_user.email = request_body.email
    mod_user.password = request_body.password

    try:
        mod_user.validate()
    except ValidationError as e:
        log.debug('mod_user validation error = %s' % e)
        if 'password' in e.messages:
            log.debug('response = invalid password')
            response.set_data(APIErrorResponse.INVALID_PASSWORD)
            return
        elif 'email' in e.messages:
            log.debug('response = invalid email')
            response.set_data(APIErrorResponse.INVALID_EMAIL)
            return
        else:
            log.debug('response = internal server error')
            response.set_data(APIErrorResponse.INTERNAL_SERVER_ERROR)
            return

    # Hash password before database insertion.
    mod_user.password = password_context(holder).encrypt(mod_user.password)

    log.debug('mod_user.email = %s' % mod_user.email)
    log.debug('mod_user.password = %s' % mod_user.password)

    sql_result = execute_statement(
        statement=User.UPDATE_BY_EMAIL,
        params=mod_user.update_by_email_params(auth_user.email),
        object_class=User,
        is_select=False)

    error_response = handle_user_sql_result_error(sql_result)

    if error_response:
        response.set_data(error_response)
        return

    log.debug('response = success')
    response.set_data(APIErrorResponse.SUCCESS)


def route_request(request, response, holder):
    """Route request by type."""

    t = request.args.get('type')

    if t is None:
        log.debug('request type is None')
        log.debug('response = malformed request')
        response.set_data(APIErrorResponse.MALFORMED_REQUEST)
        return

    if t == APIRequestType.TEST:
        test(request, response, holder)
    elif t == APIRequestType.BASE_DATA_DOWN:
        base_data_down(request, response, holder)
    elif t == APIRequestType.SYNC_DOWN:
        sync_down(request, response, holder)
    elif t == APIRequestType.SYNC_UP:
        sync_up(request, response, holder)
    elif t == APIRequestType.ACCOUNT_OPEN:
        account_open(request, response, holder)
    elif t == APIRequestType.ACCOUNT_CLOSE:
        account_close(request, response, holder)
    elif t == APIRequestType.ACCOUNT_MODIFY:
        account_modify(request, response, holder)
    else:
        log.debug('request type match not found')
        log.debug('response = malformed request')
        response.set_data(APIErrorResponse.MALFORMED_REQUEST)


@Request.application
def application(request):
    """Application entry point. Return a WSGI application callable.

    :type request: Request
    """

    log.info('application()')

    if request.method != 'POST':
        log.debug('return = Method Not Allowed')
        return MethodNotAllowed(valid_methods=['POST'])

    response = Response()

    # From here on all response data is JSON.
    response.content_type = CONTENT_TYPE_APP_JSON

    if application_key_fails(request, response):
        return response

    holder = Holder()

    holder.cursor, holder.cnx, errno = open_db()
    if errno:
        log.debug('response = internal server error')
        response.set_data(APIErrorResponse.INTERNAL_SERVER_ERROR)
        return response

    route_request(request, response, holder)
    close_db(holder.cursor, holder.cnx)
    return response


def main():
    """Run development server from the command line.

    Main does not execute when imported by a CGI script.
    """

    log.debug('main()')

    from werkzeug.serving import run_simple

    run_simple('localhost', 8080, application, use_debugger=True, use_reloader=True)


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main()
