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
import json

from dwarf import api_server
from dwarf import config
from dwarf import exception
from dwarf import utils

from dwarf.identity import api_response

CONF = config.Config()


# -----------------------------------------------------------------------------
# Bottle API routes

@exception.catchall
def _route_versions():
    """
    Route:  /
    Method: GET
    """
    utils.show_request(bottle.request)

    bottle.response.status = 300
    return api_response.list_versions()


@exception.catchall
def _route_version():
    """
    Route:  /v2.0
    Method: GET
    """
    utils.show_request(bottle.request)

    return api_response.show_version_v2d0()


@exception.catchall
def _route_tokens():
    """
    Route:  /v2.0/tokens
    Method: POST
    """
    utils.show_request(bottle.request)

    body = json.load(bottle.request.body)
    if 'auth' in body:
        return api_response.authenticate()


# -----------------------------------------------------------------------------
# API server class

class IdentityApiServer(api_server.ApiServer):
    def __init__(self):
        super(IdentityApiServer, self).__init__('Identity',
                                                CONF.bind_host,
                                                CONF.identity_api_port)

        self.app.route('/',
                       method='GET',
                       callback=_route_versions)
        self.app.route('/v2.0',
                       method='GET',
                       callback=_route_version)
        self.app.route('/v2.0/tokens',
                       method='POST',
                       callback=_route_tokens)
