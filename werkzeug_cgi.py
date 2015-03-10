#!env/bin/python

from flup.server.cgi import WSGIServer
from werkzeug_server import application

WSGIServer(application).run()
