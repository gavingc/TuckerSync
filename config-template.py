"""Tucker Sync config (template) module, used by server and client implementations.

Usage:
    Copy config-template to config.py
    Adjust config settings below.

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

APP_KEY = 'private'

db_config = {'database': 'database_name',
             'user': 'user_name',
             'password': 'secret_here',
             'host': '127.0.0.1',
             'raise_on_warnings': True}

USER_PASSWORD_LEN = 14
