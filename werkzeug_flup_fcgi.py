#!env/bin/python

from flup.server.fcgi import WSGIServer
from werkzeug_server import application

if __name__ == '__main__':
    # application = make_app()
    WSGIServer(application).run()
