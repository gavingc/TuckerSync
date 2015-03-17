#!env/bin/python

from wsgiref.handlers import CGIHandler
from werkzeug_server import application

CGIHandler().run(application)
