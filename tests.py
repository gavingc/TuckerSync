#!env/bin/python

"""Test suite for the Tucker Sync algorithm, server and client.

Usage:
    ./tests.py --help
    or
    See main().

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

import client
from common import APIRequestType, HTTP, JSON, APIRequest, APIErrorResponse, JSONKey, \
    APIErrorCode, SyncDownRequestBody, AccountOpenRequestBody
from config import APP_KEYS


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

    @pytest.fixture
    def request(self, base_url):
        request = APIRequest()
        request.base_url = base_url
        request.type = APIRequestType.TEST
        request.key = APP_KEYS[1]
        request.email = 'user@example.com'
        request.password = 'secret78901234'
        return request

    def test_get_server_root(self, request):
        """Test server 'root'."""
        response = requests.get(request.base_url, headers=request.base_headers)
        assert HTTP.OK == response.status_code
        assert 0 < len(response.content)

    def test_post_server_test_function_check_connection(self, request):
        """Test server 'test' function. Auth should fail due to no account on server."""
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code  # connection ok.
        assert APIErrorResponse.AUTH_FAIL == response.content

    def test_post_server_account_open(self, request, account_open_request_body):
        """Test server 'accountOpen' function."""
        request.type = APIRequestType.ACCOUNT_OPEN
        request.body = JSON.dumps(account_open_request_body.to_primitive())
        response = requests.post(request.base_url, request.body,
                                 params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.SUCCESS == response.content

    def test_post_server_test_function_authentication(self, request):
        """Test server 'test' function. Auth should pass."""
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.SUCCESS == response.content

    def test_post_server_account_open_uuid_not_unique(self, request, account_open_request_body):
        """Test server 'accountOpen' function with existing client UUID (created above)."""
        request.type = APIRequestType.ACCOUNT_OPEN
        request.email = 'user2@example.com'
        request.body = JSON.dumps(account_open_request_body.to_primitive())
        response = requests.post(request.base_url, request.body,
                                 params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.CLIENT_UUID_NOT_UNIQUE == response.content

    def test_post_server_test_function_invalid_password_too_short(self, request):
        """Test server 'test' function. Short invalid password. Auth simply fails don't leak why."""
        request.password = 'short'
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.AUTH_FAIL == response.content

    def test_post_server_test_function_invalid_key(self, request):
        """Test server 'test' function with an invalid key."""
        request.key = 'notPrivate'
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.INVALID_KEY == response.content

    def test_post_server_test_function_none_key(self, request):
        """Test server 'test' function with 'None' as key."""
        request.key = 'None'
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.INVALID_KEY == response.content

    def test_post_server_test_function_no_key(self, request):
        """Test server 'test' function with no key query param."""
        request.key = None
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_server_sync_down_function(self, request, sync_down_request_body):
        """Test server 'syncDown' function."""
        request.type = APIRequestType.SYNC_DOWN
        request.body = JSON.dumps(sync_down_request_body.to_primitive())
        response = requests.post(request.base_url, request.body,
                                 params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        jo = response.json()
        assert APIErrorCode.SUCCESS == jo[JSONKey.ERROR]
        assert isinstance(jo[JSONKey.OBJECTS], list)

    def test_post_server_sync_down_function_without_content_header(self, request):
        """Test server 'syncDown' function."""
        request.type = APIRequestType.SYNC_DOWN
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_server_sync_up_function(self, request):
        """Test server 'syncUp' function."""
        request.type = APIRequestType.SYNC_UP
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        # assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_server_sync_up_function_without_content_header(self, request):
        """Test server 'syncUp' function."""
        request.type = APIRequestType.SYNC_UP
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_malformed_request_type_not_specified(self, request):
        """Test server when no request type is specified."""
        request.type = None
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_malformed_request_type_not_supported(self, request):
        """Test server when an unsupported request type is specified."""
        request.type = 'notSupported'
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.MALFORMED_REQUEST == response.content

    def test_post_server_account_close(self, request):
        """Test server 'accountClose' function."""
        request.type = APIRequestType.ACCOUNT_CLOSE
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
        assert HTTP.OK == response.status_code
        assert APIErrorResponse.SUCCESS == response.content

    def test_post_server_test_function_authentication_closed_account(self, request):
        """Test server 'test' function. Auth should fail."""
        response = requests.post(request.base_url, params=request.params, headers=request.headers)
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


def main():
    """Run the test suite.

    Accepted optional command line arguments:
        --help to view help.
        --baseurl BASEURL to specify the server base url.
        -k K to only run tests which match the given substring expression.

    Usage:
        ./tests.py
        ./tests.py --help
        ./tests.py --baseurl "http://0.0.0.0:8080/"
        ./tests.py -k "TestIntegration or TestMultiple"
        ./tests.py --baseurl "http://0.0.0.0:8080/" -k "TestIntegration or TestMultiple"
    """

    # PyTest argument list: verbose, exit on first failure and caplog format.
    args = ['-vx', '--log-format=%(levelname)s:%(name)s:%(message)s']

    # Command line arguments.
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseurl", help="Specify the server base url.")
    parser.add_argument("-k", help="Only run tests which match the given substring expression.")
    cmd_args = parser.parse_args()

    # Optional command line argument specifying the server base url.
    if cmd_args.baseurl:
        args.append('--baseurl')
        args.append(cmd_args.baseurl)

    # Specify this file as the only test file.
    args.append(__file__)

    # Optional command line argument to only run tests which match the given substring expression.
    if cmd_args.k:
        args.append('-k %s' % cmd_args.k)

    # Run PyTest with the supplied args.
    # Equivalent to PyTest command line:
    # env/bin/py.test -vx --log-format="%(levelname)s:%(name)s:%(message)s"
    #   --baseurl "http://0.0.0.0:8080/" tests.py -k "TestIntegration or TestMultiple"
    pytest.main(args)

    # Run Clients
    # clientA().start()
    # clientB().start()


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main()
