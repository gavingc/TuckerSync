#!env/bin/python

from flup.server.cgi import WSGIServer
from server import application

WSGIServer(application).run()
