#!/usr/bin/python

import bottle
import logging

from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler

LOG = logging.getLogger(__name__)


class BaseHTTPRequestHandler(WSGIRequestHandler):
    def log_request(self, code='-', size='-'):
        LOG.info('%s from %s to http://%s:%s%s %s %s',
                 self.command,
                 self.client_address[0],
                 self.server.server_address[0],
                 self.server.server_address[1],
                 self.path,
                 code,
                 size)


class BaseHTTPServer(bottle.ServerAdapter):
    """
    Reimplement bottle's WSGIRefServer to add a stop() method for cleanly
    shutting down the server
    """
    srv = None

    def run(self, handler):
        self.options['handler_class'] = BaseHTTPRequestHandler
        self.srv = make_server(self.host, self.port, handler, **self.options)
        self.srv.serve_forever()

    def stop(self):
        self.srv.shutdown()
