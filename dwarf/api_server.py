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
import time
import urllib2

from wsgiref.simple_server import WSGIServer, WSGIRequestHandler

from dwarf import config

from dwarf.compute import api as api_compute
from dwarf.identity import api as api_identity
from dwarf.image import api as api_image

CONF = config.Config()
LOG = logging.getLogger(__name__)


class _HTTPRequestHandler(WSGIRequestHandler):
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


class _HTTPServer(bottle.ServerAdapter):
    """
    Reimplement bottle's WSGIRefServer. Override the request handler class and
    add a stop() method for cleanly shutting down the server.
    """
    srv = None
    app = None

    def run(self, handler):
        # Handle the TIME_WAIT state for quick server restarts
        WSGIServer.allow_reuse_address = 1

        # Create the server and start it
        self.srv = WSGIServer((self.host, self.port), _HTTPRequestHandler)
        self.srv.set_app(self.app)
        try:
            self.srv.serve_forever()
        finally:
            self.srv.server_close()

    def stop(self):
        if self.srv:
            self.srv.shutdown()


class ApiServer(threading.Thread):
    """
    The API server class
    """

    def __init__(self, quiet=False):
        threading.Thread.__init__(self)

        self.quiet = quiet

        self.daemon = True
        self.server = None
        self.app = bottle.Bottle()
        self.host = CONF.bind_host
        self.port = CONF.bind_port

        # Set the routes for the different services
        api_compute.set_routes(self.app)
        api_identity.set_routes(self.app)
        api_image.set_routes(self.app)

    def setup(self):
        api_compute.setup()
        api_identity.setup()
        api_image.setup()

    def teardown(self):
        api_compute.teardown()
        api_identity.teardown()
        api_image.teardown()

    def run(self):
        """
        Start the server
        """
        try:
            self.setup()
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to setup API server')
            return

        LOG.info('Starting API server')
        try:
            # Check if we can bind to the address. We need to retry for a bit
            # until the dwarf network comes up.
            sock = socket.socket(socket.AF_INET)
            # Allow reusing the same address so that we can quickly restart a
            # server and don't have to wait due to the TIME_WAIT state.
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            for i in range(1, 100):
                try:
                    sock.bind((self.host, self.port))
                    sock.close()
                    break
                except Exception:   # pylint: disable=W0703
                    # Give up after 15 attempts
                    if i == 30:
                        raise
                    time.sleep(1)

            # Create the HTTP server
            self.server = _HTTPServer(host=self.host, port=self.port)
            self.server.app = self.app

            # Start the bottle server
            LOG.info('API server listening on %s:%s', self.host, self.port)
            bottle.run(server=self.server, quiet=self.quiet)
            LOG.info('API server shut down')

        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to start API server')

        finally:
            self.teardown()

    def stop(self):
        """
        Stop the server
        """
        if self.is_alive():
            LOG.info('Stopping API server')
            self.server.stop()

    def is_active(self):
        """
        Check if the server responds to queries
        """
        if not self.is_alive():
            return False

        try:
            urllib2.urlopen('http://%s:%d/' % (self.host, self.port),
                            timeout=2)
        except urllib2.HTTPError:
            # HTTPError means we did get a response, so the server is alive
            pass
        except Exception:   # pylint: disable=W0703
            # Any other exception means the server is not responding
            return False

        return True
