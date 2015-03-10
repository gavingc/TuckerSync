#!env/bin/python

from werkzeug.wrappers import Response


def application(environ, start_response):
    response = Response('Hello World by Werkzeug!', mimetype='text/plain')
    return response(environ, start_response)
