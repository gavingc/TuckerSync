#!env/bin/python

"""Test suite for the Tucker Sync algorithm, server and client.

Usage:
    ./test.py --help
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
from common import APIQuery, HTTP, JSON


class TestServer(object):
    """Server functional tests.

    base_url is a test fixture defined in conftest.py
    """

    def test_get_server_root(self, base_url):
        """Test server 'root'."""
        response = requests.get(base_url)
        assert HTTP.OK == response.status_code

    def test_get_server_test_function(self, base_url):
        """Test server 'test' function."""
        response = requests.get(base_url + APIQuery.TEST)
        assert HTTP.OK == response.status_code

    def test_get_server_sync_down_function(self, base_url):
        """Test server 'syncDown' function."""
        response = requests.get(base_url + APIQuery.SYNC_DOWN)
        assert HTTP.OK == response.status_code

    def test_get_server_sync_up_function(self, base_url):
        """Test server 'syncUp' function."""
        response = requests.get(base_url + APIQuery.SYNC_UP)
        assert HTTP.OK == response.status_code


class TestClient(object):
    """Client unit tests."""

    @pytest.fixture(scope="class")
    def client_a(self, base_url):
        return client.Client(base_url)

    @pytest.fixture(scope="class")
    def client_b(self, base_url):
        return client.Client(base_url)

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
        return client.Client(base_url)

    def test_connection(self, client_a):
        """Test client's connection to server."""
        result = client_a.check_connection()
        assert True == result


class TestMultipleClientIntegration(object):
    """Test the API by exercising multiple clients and server."""

    @pytest.fixture(scope="class")
    def client_a(self, base_url):
        return client.Client(base_url)

    @pytest.fixture(scope="class")
    def client_b(self, base_url):
        return client.Client(base_url)

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
            client_c = client.Client(url)
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
    #clientA().start()
    #clientB().start()


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main()
