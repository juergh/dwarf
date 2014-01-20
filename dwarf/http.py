#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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
