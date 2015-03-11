#!env/bin/python

"""Tucker Sync (werkzeug based) server module.

Implemented with Werkzeug Python WSGI Utility Library.

Usage:
    Launch from CGI script:
        #!env/bin/python

        from flup.server.cgi import WSGIServer
        from werkzeug_server import application

        WSGIServer(application).run()

    Run development server from the command line:
        ./werkzeug_server.py

License:
    The MIT License (MIT), see LICENSE.txt for more details.

Copyright:
    Copyright (c) 2014 Steven Tucker and Gavin Kromhout.
"""

import logging
from os.path import basename

from werkzeug.wrappers import Request, Response

from app_config import LOG_FILE_NAME, LOG_LEVEL, PRODUCTION


def logging_init():
    """Init logging with app_config settings."""

    # Get log level from config.
    log_level = getattr(logging, LOG_LEVEL.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError('invalid log level: %s' % LOG_LEVEL)

    if PRODUCTION:
        from logging.handlers import RotatingFileHandler
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        handler = RotatingFileHandler(LOG_FILE_NAME, maxBytes=300000, backupCount=1)
        root_logger.addHandler(handler)
    else:
        from sys import stderr
        logging.basicConfig(stream=stderr, level=log_level)

# Module logger.
logging_init()
log = logging.getLogger(basename(__file__).split('.')[0])


@Request.application
def application(request):
    """Application entry point.

    :type request: Request
    """

    resp_body = 'Hello World by Werkzeug! Method:' + str(request.accept_mimetypes)
    return Response(resp_body, mimetype='text/plain')


def main():
    """Run the server from the command line.

    Main does not execute when imported by a CGI script.
    """

    from werkzeug.serving import run_simple
    run_simple('localhost', 8080, application)


# Run main when commands read either from standard input,
# from a script file, or from an interactive prompt.
if __name__ == "__main__":
    main()
