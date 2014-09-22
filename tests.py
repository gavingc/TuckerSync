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
import requests
import unittest

import client
from common import APIQuery, HTTP

# Customisable
BASE_URL = "http://0.0.0.0:8080/"


class ServerTests(unittest.TestCase):
    """Server unit tests."""

    def test_0010_get_server_root(self):
        """Test server 'root'."""
        response = requests.get(BASE_URL)
        self.assertEquals(HTTP.OK, response.status_code)

    def test_0020_get_server_test_function(self):
        """Test server 'test' function."""
        response = requests.get(BASE_URL + APIQuery.TEST)
        self.assertEquals(HTTP.OK, response.status_code)

    def test_0030_get_server_sync_down_function(self):
        """Test server 'syncDown' function."""
        response = requests.get(BASE_URL + APIQuery.SYNC_DOWN)
        self.assertEquals(HTTP.OK, response.status_code)

    def test_0040_get_server_sync_up_function(self):
        """Test server 'syncUp' function."""
        response = requests.get(BASE_URL + APIQuery.SYNC_UP)
        self.assertEquals(HTTP.OK, response.status_code)


class IntegrationTests(unittest.TestCase):
    """Test the API by exercising the client and server.

    These tests are more integration than unit tests.
    Python unittest is just used as the test runner.
    """

    def setUp(self):
        # TODO start server, for now start manually using IDE Run Server run configuration.
        self.client_A = client.Client(BASE_URL)

    def test_0010_connection(self):
        """Test client's connection to server."""
        self.assertEquals(True, self.client_A.check_connection())

    def tearDown(self):
        # TODO stop server.
        pass

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

    # Easy way to run unit tests.
    ##unittest.main()

    # Nice way to run unit tests.
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ServerTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IntegrationTests)
    unittest.TextTestRunner(verbosity=2).run(suite)

    # Run Clients
    #clientA().start()
    #clientB().start()

if __name__ == "__main__":
    # Run main when commands read either from standard input,
    # from a script file, or from an interactive prompt.
    main()
