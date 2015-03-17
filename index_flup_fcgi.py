#!env/bin/python

from flup.server.fcgi import WSGIServer
from werkzeug_server import application

WSGIServer(application).run()
