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
import pytest

# Default server base url, may be overridden by command line arg.
BASE_URL = "http://0.0.0.0:8080/"


def pytest_addoption(parser):
    """Server base url command line option."""
    parser.addoption("--baseurl", action="store", default=BASE_URL,
                     help="Server base url default: " + BASE_URL)


@pytest.fixture(scope="session")
def base_url(request):
    """Server base url fixture."""
    return request.config.getoption("--baseurl")
