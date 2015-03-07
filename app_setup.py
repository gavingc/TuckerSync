#!env/bin/python

"""Tucker Sync application setup module.

Setup the server or development environment.
May be run from the command line (or as a CGI script? - untested).

Usage:
    ./app_setup.py
    app_setup.py [-h] [-v] [--only-tables]

Optional arguments:
    -h, --help     show this help message and exit
    -v, --verbose  log debug messages
    --only-tables  only drop-create database tables

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

import sys
import shutil
import argparse
import logging
from os.path import basename, isfile

# Constants
CONFIG_FNAME = 'app_config.py'
CONFIG_TEMPLATE_FNAME = 'app_config_template.py'

# Module logger.
log = logging.getLogger(basename(__file__).split('.')[0])


def check_connection():
    """Check the database connection."""

    from server import open_db

    cursor, cnx, errno = open_db()

    if errno:
        log.error('could not connect to database')
        log.error(' - check your database settings')
        log.error(' - edit or (re)move the config file: %s', CONFIG_FNAME)
        log.error(' - then re-run ./app_setup.py')
        sys.exit()


def drop_create_tables():
    """Drop and create database tables helper function."""

    from server import open_db, close_db

    log.info('dropping and creating database tables')

    # Config opens connection with raise_on_warnings=True
    cursor, cnx, errno = open_db()
    assert None == errno

    files = ('app_drop.sql', 'base_drop.sql', 'base_create.sql', 'app_create.sql')

    # MySQL generates warnings for DROP IF EXISTS statements against nonexistent tables.
    # These warnings are 'Note level'.
    # http://dev.mysql.com/doc/refman/5.6/en/drop-table.html
    # http://bugs.mysql.com/bug.php?id=2839
    # http://dev.mysql.com/doc/refman/5.0/en/server-system-variables.html#sysvar_sql_notes

    # Connector/Python has an issue/bug fetching warnings when multi=True and then actually
    # executing multiple statements with any warnings.
    # An InterfaceError is raised and execution cannot continue.

    # To prevent this get_warnings may be disabled for multi=True, or `SET sql_notes = 0`.
    # Setting/Clearing raise_on_warnings also sets/clears get_warnings.
    # cnx.raise_on_warnings = False
    # OR
    stmt = """SET sql_notes = 0"""
    cursor.execute(stmt)

    for fl in files:
        with open(fl) as f:
            statements = f.read()

        for result in cursor.execute(statements, multi=True):
            # Errors will raise but no warning checking is available.
            # MySQL warnings greater than note level may raise a misleading error.
            assert -1 != result.rowcount

    close_db(cursor, cnx)


def config_file():
    """Setup config file from template."""

    if isfile(CONFIG_FNAME):
        log.info('found existing config file')
        return

    log.info('copying %s -> %s', CONFIG_TEMPLATE_FNAME, CONFIG_FNAME)
    shutil.copy2(CONFIG_TEMPLATE_FNAME, CONFIG_FNAME)


def init_logging(cmd_args):
    """Init logging."""

    from sys import stderr

    if cmd_args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    logging.basicConfig(stream=stderr, level=log_level)


def get_cmd_args():
    """Get the command line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument('-v',
                        '--verbose',
                        help='log debug messages',
                        action='store_true')
    parser.add_argument('--only-tables',
                        help='only drop-create database tables',
                        action='store_true')

    return parser.parse_args()


def run_setup(cmd_args):
    """Run the setup functions."""

    if cmd_args.only_tables:
        log.info('only running drop-create database tables')
        check_connection()
        drop_create_tables()
        return

    config_file()
    check_connection()
    drop_create_tables()


def main():
    """Main function."""

    print '\nTucker Sync - Application Setup\n'

    cmd_args = get_cmd_args()
    init_logging(cmd_args)
    run_setup(cmd_args)

    print '\nTucker Sync - Setup Complete\n'


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main()
