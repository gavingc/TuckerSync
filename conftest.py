"""Pytest conf module.

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

from __future__ import print_function

import logging
from os.path import basename
import pytest

import app_setup

fixture = pytest.fixture

# Default server base url, may be overridden by command line arg.
BASE_URL = "http://0.0.0.0:8080/"

# Module logger.
log = logging.getLogger(basename(__file__).split('.')[0])


def pytest_addoption(parser):
    """Server base url command line option."""

    parser.addoption("--remote-server", action="store_true",
                     help="use when running against a remote server")
    parser.addoption("--baseurl", action="store", default=BASE_URL,
                     help="Server base url default: " + BASE_URL)


@fixture(scope="session")
def remote_server(request):
    """Remote server option fixture."""

    return request.config.getoption("--remote-server")


@fixture(scope="session")
def base_url(request):
    """Server base url option fixture."""

    return request.config.getoption("--baseurl")


def pytest_report_header(config):
    """Test report header."""

    rh = "Testing server base url: " + config.getoption("--baseurl")

    if config.getoption("--remote-server"):
        rh += '\n WARNING: Not cleaning tables on remote server.'
        rh += '\n On remote server run : `app_setup.py --only-tables` \n'

    return rh


@fixture
def before_test_drop_create_tables(remote_server):
    """Drop-create database tables before test fixture."""

    if remote_server:
        assert False, ('Test requires clean tables. '
                       'Cannot drop tables of a remote server.')

    app_setup.drop_create_tables()


@fixture(scope='session')
def session_fin_drop_create_tables(request, remote_server):
    """Drop-create database tables session finalizer fixture."""

    def fin():
        if not remote_server:
            print()  # pytest missing newline in output
            print()  # spacer
            log.info('session_fin_drop_create_tables()')
            app_setup.drop_create_tables()

    request.addfinalizer(fin)
