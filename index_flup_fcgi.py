#!env/bin/python

from flup.server.fcgi import WSGIServer
from server import application

WSGIServer(application).run()
