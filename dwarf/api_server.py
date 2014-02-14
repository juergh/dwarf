#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bottle
import logging
import threading

from wsgiref.simple_server import make_server
from wsgiref.simple_server import WSGIRequestHandler

LOG = logging.getLogger(__name__)


class _BaseHTTPRequestHandler(WSGIRequestHandler):
    """
    Custom logging for the request handler
    """
    def log_request(self, code='-', size='-'):
        LOG.info('%s from %s to http://%s:%s%s %s %s',
                 self.command,
                 self.client_address[0],
                 self.server.server_address[0],
                 self.server.server_address[1],
                 self.path,
                 code,
                 size)


class _BaseHTTPServer(bottle.ServerAdapter):
    """
    Reimplement bottle's WSGIRefServer to add a stop() method for cleanly
    shutting down the server
    """
    srv = None

    def run(self, handler):
        self.options['handler_class'] = _BaseHTTPRequestHandler
        self.srv = make_server(self.host, self.port, handler, **self.options)
        self.srv.serve_forever()

    def stop(self):
        self.srv.shutdown()


class ApiServer(threading.Thread):
    app = bottle.Bottle()
    server = None
    name = ''
    host = ''
    port = 0

    def run(self):
        """
        Start the server
        """
        LOG.info('Starting %s API server', self.name)

        try:
            self.server = _BaseHTTPServer(host=self.host, port=self.port)

            LOG.info('%s API server listening on %s:%s', self.name, self.host,
                     self.port)
            bottle.run(self.app, server=self.server)
            LOG.info('%s API server shut down', self.name)
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to start %s API server', self.name)

    def stop(self):
        """
        Stop the server
        """
        try:
            self.server.stop()
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to stop %s API server', self.name)
