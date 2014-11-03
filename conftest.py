"""Pytest conf module.

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

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


def pytest_report_header(config):
    """Test report header."""
    return "Testing server base url: " + config.getoption("--baseurl")
