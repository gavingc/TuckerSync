#!env/bin/python

"""Tucker Sync test module.

Main test suite for the algorithm, server and client.

Usage:
    tests.py [-h] [--baseurl BASEURL] [-k K]

Optional arguments:
  -h, --help         show this help message and exit
  --baseurl BASEURL  specify the server base url
  -k K               only run tests which match the given substring expression

Usage examples:
    ./tests.py
    ./tests.py --help
    ./tests.py --baseurl "http://0.0.0.0:8080/"
    ./tests.py -k "TestIntegration or TestMultiple"
    ./tests.py --baseurl "http://0.0.0.0:8080/" -k "Integration and not Multiple"

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

import argparse
import pytest
import requests
import uuid
from flexmock import flexmock
from werkzeug.exceptions import MethodNotAllowed

import client
from common import APIRequestType, HTTP, JSON, APIRequest, APIErrorResponse, JSONKey, \
    APIErrorCode, SyncDownRequestBody, AccountOpenRequestBody, SyncUpRequestBody
from app_config import APP_KEYS


class TestCommon(object):
    """Common unit tests."""

    def test_api_error_response(self):
        assert '{"error":0}' == APIErrorResponse.SUCCESS
        assert '{"error":1}' == APIErrorResponse.INTERNAL_SERVER_ERROR
        assert '{"error":2}' == APIErrorResponse.MALFORMED_REQUEST


class TestServer(object):
    """Server functional tests.

    base_url is a test fixture defined in conftest.py
    """

    @pytest.fixture(scope='class')
    def account_open_request_body(self):
        rb = AccountOpenRequestBody()
        rb.clientUUID = uuid.uuid4()
        return rb

    @pytest.fixture(scope='class')
    def sync_down_request_body(self, account_open_request_body):
        rb = SyncDownRequestBody()
        rb.objectClass = 'Product'
        rb.clientUUID = account_open_request_body.clientUUID
        rb.lastSync = 0
        return rb

    @pytest.fixture(scope='class')
    def sync_up_request_body(self, account_open_request_body):
        rb = SyncUpRequestBody()
        rb.objectClass = 'Product'
        rb.clientUUID = account_open_request_body.clientUUID
        rb.objects = []
        return rb

    @pytest.fixture
    def req(self, base_url):
        req = APIRequest()
        req.base_url = base_url
        req.type = APIRequestType.TEST
        req.key = APP_KEYS[1]
        req.email = 'user@example.com'
        req.password = 'secret78901234'
        return req

    METHODS_NOT_ALLOWED = ['', ' ', '*', 'None',
                           'OPTIONS', 'GET', 'HEAD', 'PUT',
                           'PATCH', 'DELETE', 'TRACE', 'CONNECT']

    @pytest.mark.parametrize("method", METHODS_NOT_ALLOWED)
    def test_server_root_method_not_allowed(self, req, method):
        """Test server 'root'."""

        response = requests.request(method, req.base_url, headers=req.base_headers)

        # Python server (Werkzeug) correctly claims to return a 400 Bad Request.
        # However Requests lib does not correctly parse the response.status_code
        if method in ['', ' ']:
            assert '400' in response.content
            return

        assert MethodNotAllowed.code == response.status_code
        assert 'POST' == response.headers.get('Allow')
        if method is not 'HEAD':
            assert 'Method Not Allowed' in response.content

    def test_post_server_test_function_check_connection(self, req):
        """Test server 'test' function. Auth should fail due to no account on server."""
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code  # connection ok.
        assert APIErrorResponse.AUTH_FAIL == response.content

    def test_post_server_account_open(self, req, account_open_request_body):
        """Test server 'accountOpen' function."""
        req.type = APIRequestType.ACCOUNT_OPEN
        req.body = JSON.dumps(account_open_request_body.to_primitive())
        response = requests.post(req.base_url, req.body,
                                 params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.SUCCESS == response.content

    def test_post_server_test_function_authentication(self, req):
        """Test server 'test' function. Auth should pass."""
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.SUCCESS == response.content

    def test_post_server_account_open_email_not_unique(self, req):
        """Test server 'accountOpen' function with existing client email (created above)."""
        req.type = APIRequestType.ACCOUNT_OPEN
        account_open_request_body = AccountOpenRequestBody()
        account_open_request_body.clientUUID = uuid.uuid4()  # unique uuid
        req.body = JSON.dumps(account_open_request_body.to_primitive())
        response = requests.post(req.base_url, req.body,
                                 params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.EMAIL_NOT_UNIQUE == response.content

    def test_post_server_account_open_uuid_not_unique(self, req, account_open_request_body):
        """Test server 'accountOpen' function with existing client UUID (created above)."""
        req.type = APIRequestType.ACCOUNT_OPEN
        req.email = 'user2@example.com'
        req.body = JSON.dumps(account_open_request_body.to_primitive())
        response = requests.post(req.base_url, req.body,
                                 params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.CLIENT_UUID_NOT_UNIQUE == response.content

    def test_post_server_test_function_invalid_password_too_short(self, req):
        """Test server 'test' function. Short invalid password. Auth simply fails don't leak why."""
        req.password = 'short'
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.AUTH_FAIL == response.content

    def test_post_server_test_function_invalid_key(self, req):
        """Test server 'test' function with an invalid key."""
        req.key = 'notPrivate'
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.INVALID_KEY == response.content

    def test_post_server_test_function_none_key(self, req):
        """Test server 'test' function with 'None' as key."""
        req.key = 'None'
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.INVALID_KEY == response.content

    def test_post_server_test_function_no_key(self, req):
        """Test server 'test' function with no key query param."""
        req.key = None
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_server_sync_down_function(self, req, sync_down_request_body):
        """Test server 'syncDown' function."""
        req.type = APIRequestType.SYNC_DOWN
        req.body = JSON.dumps(sync_down_request_body.to_primitive())
        response = requests.post(req.base_url, req.body,
                                 params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        jo = response.json()
        assert APIErrorCode.SUCCESS == jo[JSONKey.ERROR]
        assert isinstance(jo[JSONKey.OBJECTS], list)

    def test_post_server_sync_down_function_without_content_header(self, req):
        """Test server 'syncDown' function."""
        req.type = APIRequestType.SYNC_DOWN
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_server_sync_up_function(self, req, sync_up_request_body):
        """Test server 'syncUp' function."""
        req.type = APIRequestType.SYNC_UP
        req.body = JSON.dumps(sync_up_request_body.to_primitive())
        response = requests.post(req.base_url, req.body,
                                 params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        jo = response.json()
        assert APIErrorCode.SUCCESS == jo[JSONKey.ERROR]
        assert isinstance(jo[JSONKey.OBJECTS], list)

    def test_post_server_sync_up_function_without_content_header(self, req):
        """Test server 'syncUp' function."""
        req.type = APIRequestType.SYNC_UP
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_malformed_request_type_not_specified(self, req):
        """Test server when no request type is specified."""
        req.type = None
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_malformed_request_type_not_supported(self, req):
        """Test server when an unsupported request type is specified."""
        req.type = 'notSupported'
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_server_account_close(self, req):
        """Test server 'accountClose' function."""
        req.type = APIRequestType.ACCOUNT_CLOSE
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.SUCCESS == response.content

    def test_post_server_test_function_authentication_closed_account(self, req):
        """Test server 'test' function. Auth should fail."""
        response = requests.post(req.base_url, params=req.params, headers=req.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.AUTH_FAIL == response.content


class TestClient(object):
    """Client unit tests."""

    @pytest.fixture(scope="class")
    def client_a(self, base_url):
        return client.Client(base_url, APP_KEYS[1], 'user@example.com', 'secret78901234')

    @pytest.fixture(scope="class")
    def client_b(self, base_url):
        return client.Client(base_url, APP_KEYS[0], 'user@example.com', 'secret78901234')

    @pytest.fixture(scope="function")
    def mock_response(self):
        return flexmock(status_code=200, content='{"error":0}')

    def test_client_creation(self, client_a):
        assert client_a

    def test_client_uuid(self, client_a):
        assert isinstance(client_a.UUID, uuid.UUID)

    def test_client_uuid_is_unique(self, client_a, client_b):
        assert client_a.UUID != client_b.UUID

    def test_client_get_json(self, client_a, mock_response):
        jo = client_a.get_json_object(mock_response)
        assert mock_response.content == JSON.dumps(jo)

    def test_client_get_json_non_ok_status_code(self, client_a, mock_response):
        mock_response.status_code = 401
        with pytest.raises(Exception):
            client_a.get_json_object(mock_response)

    def test_client_get_json_empty_content(self, client_a, mock_response):
        mock_response.content = ''
        with pytest.raises(Exception):
            client_a.get_json_object(mock_response)

    def test_client_get_json_non_object_content(self, client_a, mock_response):
        mock_response.content = '[]'
        with pytest.raises(Exception):
            client_a.get_json_object(mock_response)

    def test_client_get_json_no_error_key_content(self, client_a, mock_response):
        mock_response.content = '{}'
        with pytest.raises(Exception):
            client_a.get_json_object(mock_response)


class TestIntegration(object):
    """Test the API by exercising the client and server."""

    @pytest.fixture(scope="class")
    def client_a(self, base_url):
        return client.Client(base_url,
                             APP_KEYS[1],
                             str(uuid.uuid4()) + '@example.com',
                             'secret78901234')

    @pytest.fixture(scope="class")
    def client_b(self, base_url):
        return client.Client(base_url,
                             APP_KEYS[0],
                             str(uuid.uuid4()) + '@example.com',
                             'secret78901234')

    def test_connection_a(self, client_a):
        """Test client_a's connection to server."""
        result = client_a.check_connection()
        assert True == result

    def test_connection_b(self, client_b):
        """Test client_b's connection to server."""
        result = client_b.check_connection()
        assert True == result

    def test_account_open(self, client_a):
        """Test opening an account."""
        result = client_a.account_open()
        assert True == result

    def test_account_authentication(self, client_a):
        """Test authentication of the account created above."""
        result = client_a.check_authentication()
        assert True == result

    def test_account_authentication_wrong_password(self, client_a):
        """Test authentication of the account created above with wrong password."""
        saved_password = client_a.password
        client_a.password = 'secret789012345'  # set wrong password
        result = client_a.check_authentication()
        client_a.password = saved_password
        assert False == result

    def test_account_open_email_not_unique(self, client_a):
        """Test opening an account with the same email as above."""
        result = client_a.account_open()
        assert False == result

    def test_account_open_invalid_password_too_short(self, client_b):
        """Test opening an account with a password that is too short."""
        saved_password = client_b.password
        client_b.password = 'secret7890123'  # set short password
        result = client_b.account_open()
        client_b.password = saved_password
        assert False == result

    def test_account_open_invalid_email_syntax(self, client_b):
        """Test opening an account with an invalid email syntax."""
        saved_email = client_b.email
        client_b.email = str(uuid.uuid4()) + 'example.com'  # missing '@'
        result = client_b.account_open()
        client_b.email = saved_email
        assert False == result

    def test_account_modify_password(self, client_a):
        """Test modifying the account password created by client_a."""
        new_password = 'secret78901235'
        result = client_a.account_modify(client_a.email, new_password)
        client_a.password = new_password
        assert True == result

    def test_account_authentication_changed_password(self, client_a):
        """Test authentication of the account modified above."""
        result = client_a.check_authentication()
        assert True == result

    def test_account_modify_email(self, client_a):
        """Test modifying the account email created by client_a."""
        new_email = str(uuid.uuid4()) + '@example.com'
        result = client_a.account_modify(new_email, client_a.password)
        client_a.email = new_email
        assert True == result

    def test_account_authentication_changed_email(self, client_a):
        """Test authentication of the account modified above."""
        result = client_a.check_authentication()
        assert True == result

    def test_account_modify_password_and_email(self, client_a):
        """Test modifying the account created by client_a."""
        new_password = 'secret78901236'
        new_email = str(uuid.uuid4()) + '@example.com'
        result = client_a.account_modify(new_email, new_password)
        client_a.password = new_password
        client_a.email = new_email
        assert True == result

    def test_account_authentication_changed_password_and_email(self, client_a):
        """Test authentication of the account modified above."""
        result = client_a.check_authentication()
        assert True == result

    def test_account_modify_wrong_password(self, client_a):
        """Test modify of the account created above with wrong password."""
        new_password = 'secret78901238'
        new_email = str(uuid.uuid4()) + '@example.com'
        saved_password = client_a.password
        client_a.password = 'secret78901237'  # set wrong password
        result = client_a.account_modify(new_email, new_password)
        client_a.password = saved_password
        assert False == result

    def test_account_authentication_unchanged_password_and_email(self, client_a):
        """Test authentication of the unchanged account above."""
        result = client_a.check_authentication()
        assert True == result

    def test_account_modify_email_with_no_account(self, client_b):
        """Test modifying an account with an email that does not have an account."""
        result = client_b.account_modify(client_b.email, client_b.password)
        assert False == result

    def test_account_close_wrong_password(self, client_a):
        """Test closing of the account created by client_a with wrong password."""
        saved_password = client_a.password
        client_a.password = 'secret78901237'  # set wrong password
        result = client_a.account_close()
        client_a.password = saved_password
        assert False == result

    def test_account_authentication_unclosed_account(self, client_a):
        """Test authentication of the unclosed account above."""
        result = client_a.check_authentication()
        assert True == result

    def test_account_close(self, client_a):
        """Test closing an account."""
        result = client_a.account_close()
        assert True == result

    def test_account_authentication_closed_account(self, client_a):
        """Test authentication of the account closed above."""
        result = client_a.check_authentication()
        assert False == result


class TestMultipleClientIntegration(object):
    """Test the API by exercising multiple clients and server."""

    @pytest.fixture(scope="class")
    def client_a(self, base_url):
        return client.Client(base_url, APP_KEYS[1], 'user@example.com', 'secret78901234')

    @pytest.fixture(scope="class")
    def client_b(self, base_url):
        return client.Client(base_url, APP_KEYS[0], 'user@example.com', 'secret78901234')

    def test_connection_with_sequential_clients(self, client_a, client_b):
        for x in xrange(8):
            r1 = client_a.check_connection()
            r2 = client_b.check_connection()
            assert True == r1
            assert True == r2

    def test_connection_with_parallel_clients(self, client_a, base_url):
        """Client A is run in the test process while client C is run in another process.

        This allows genuine parallel execution of the client module code in Python.
        Connections to the server are effectively a race condition for each client."""

        from multiprocessing import Process, Queue

        def run_client_a():
            short_uuid = str(client_a.UUID)[:6]
            for x in xrange(8):
                print 'client a, short UUID:', short_uuid
                r1 = client_a.check_connection()
                assert True == r1

        def run_client_c(q, url):
            r = True
            client_c = client.Client(url, APP_KEYS[1], 'user@example.com', 'secret78901234')
            short_uuid = str(client_c.UUID)[:6]
            for x in xrange(8):
                print 'client c, short UUID:', short_uuid
                if client_c.check_connection() is False:
                    r = False
            q.put(r)

        queue = Queue()
        Process(target=run_client_c, args=(queue, base_url)).start()

        run_client_a()

        client_c_result = queue.get()
        assert True == client_c_result


def get_cmd_args():
    """Get the command line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--baseurl", help="specify the server base url")
    parser.add_argument("-k", help="only run tests which match the given substring expression")

    return parser.parse_args()


def get_pytest_args(file_name, cmd_args):
    """Build and return the pytest arguments."""

    # PyTest argument list: verbose, exit on first failure and caplog format.
    args = ['-vx', '--log-format=%(levelname)s:%(name)s:%(message)s']

    # Optional command line argument specifying the server base url.
    if cmd_args.baseurl:
        args.append('--baseurl')
        args.append(cmd_args.baseurl)

    # Specify this file as the only test file.
    args.append(file_name)

    # Optional command line argument to only run tests which match the given substring expression.
    if cmd_args.k:
        args.append('-k %s' % cmd_args.k)

    return args


def main(file_name):
    """Run the test suite."""

    cmd_args = get_cmd_args()
    args = get_pytest_args(file_name, cmd_args)

    # Run PyTest with the supplied args.
    # Equivalent to PyTest command line:
    # env/bin/py.test -vx --log-format="%(levelname)s:%(name)s:%(message)s"
    #   --baseurl "http://0.0.0.0:8080/" tests.py -k "TestIntegration or TestMultiple"
    pytest.main(args)


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main(__file__)
