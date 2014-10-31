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
import socket
import threading

from time import sleep

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
        if self.srv:
            self.srv.shutdown()


class ApiServer(threading.Thread):
    """
    Generic API server class
    """

    def __init__(self, sname, host, port):
        threading.Thread.__init__(self)

        self.server = None
        self.app = bottle.Bottle()

        self.sname = sname
        self.host = host
        self.port = port

    def setup(self):
        pass

    def teardown(self):
        pass

    def run(self):
        """
        Start the server
        """
        self.setup()

        LOG.info('Starting %s API server', self.sname)

        # Check if we can bind to the address. We need to retry for a bit until
        # the dwarf network comes up.
        sock = socket.socket(socket.AF_INET)
        for dummy in range(0, 15):
            try:
                sock.bind((self.host, self.port))
                sock.close()
                break
            except Exception:   # pylint: disable=W0703
                sleep(1)

        try:
            self.server = _BaseHTTPServer(host=self.host, port=self.port)

            # Start the bottle server
            LOG.info('%s API server listening on %s:%s', self.sname, self.host,
                     self.port)
            bottle.run(self.app, server=self.server)
            LOG.info('%s API server shut down', self.sname)

        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to start %s API server', self.sname)

    def stop(self):
        """
        Stop the server
        """
        try:
            self.server.stop()
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to stop %s API server', self.sname)

        self.teardown()
