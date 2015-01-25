"""Tucker Sync config (template) module, used by server and client implementations.

Usage:
    Copy config-template to config.py
    Adjust config settings below.

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

# Private Application Keys.
# Change both for production.
# Any key listed will be accepted by the server.
# To revoke a key for a group of clients simply remove or change it.
# Two or more keys should be specified (test suite requires at least 2).
#            group_a    group_b
APP_KEYS = ('private', 'zqX2*I#y9ctNrsCKHU3xWKwgH8#JJhtVlIb980^OVT*YQ')

db_config = {'database': 'database_name',
             'user': 'user_name',
             'password': 'secret_here',
             'host': '127.0.0.1',
             'raise_on_warnings': True}

# Min password length required from users.
# Test suite requires the default of 14.
USER_PASSWORD_MIN_LEN = 14

LOG_LEVEL = 'DEBUG'  # Default: LOG_LEVEL = 'DEBUG'
LOG_FILE_NAME = 'tucker-sync-server.log'

# Set True for production.
# Log to LOG_FILE_NAME if True, stderr if False.
# Passwords will be logged in clear text if False.
PRODUCTION = False
