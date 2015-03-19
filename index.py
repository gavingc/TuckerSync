#!env/bin/python

from wsgiref.handlers import CGIHandler
from server import application

CGIHandler().run(application)
