#!env/bin/python
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
import sys
import pytest
import requests
import uuid
from flexmock import flexmock

import client
from common import APIQuery, HTTP, JSON


class TestServer(object):
    """Server unit tests.

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
        # TODO start server, for now start manually using IDE Run Server run configuration.
        return client.Client(base_url)

    def test_connection(self, client_a):
        """Test client's connection to server."""
        assert True == client_a.check_connection()


# # Client A Thread
# class clientA(Thread):
#     def run(self):
#         for x in xrange(0, 11):
#             runClientA()
#             time.sleep(1)
#
# # Client B Thread
# class clientB(Thread):
#     def run(self):
#         for x in xrange(100, 103):
#             runClientB()
#             time.sleep(5)
#
#
# def runClientA():
#     print('Run Client A UUID: ' + str(clientAUuid))
#     http = httplib2.Http()
#     resp_headers, content = http.request(BASE_URL, OK)
#     print(content)
#
#
# def runClientB():
#     print('Run Client B UUID: ' + str(clientBUuid))
#     http = httplib2.Http()
#     resp_headers, content = http.request(BASE_URL, GET)
#     print(content)


def main():
    """Called when this module is the primary one."""

    # PyTest argument list: verbose, exit on first failure.
    args = ['-vx']

    # Optional single command line argument specifying the server base url.
    # Example command line: ./tests.py "http://0.0.0.0:8080/"
    if len(sys.argv) > 1:
        args.append('--baseurl')
        args.append(sys.argv[1])

    # Specify this file as the only test file.
    args.append(__file__)

    # Run PyTest with the supplied args.
    # Equivalent to PyTest command line:
    # env/bin/py.test -vx --baseurl "http://0.0.0.0:8080/" tests.py
    pytest.main(args)

    # Run Clients
    #clientA().start()
    #clientB().start()

if __name__ == "__main__":
    # Run main when commands read either from standard input,
    # from a script file, or from an interactive prompt.
    main()
