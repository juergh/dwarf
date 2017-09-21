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
    Route:  /identity
    Method: GET
    """
    utils.show_request(bottle.request)

    bottle.response.status = 300
    return api_response.list_versions()


@exception.catchall
def _route_version():
    """
    Route:  /identity/v2.0
    Method: GET
    """
    utils.show_request(bottle.request)

    return api_response.show_version_v2d0()


@exception.catchall
def _route_tokens():
    """
    Route:  /identity/v2.0/tokens
    Method: POST
    """
    utils.show_request(bottle.request)

    body = json.load(bottle.request.body)
    if 'auth' in body:
        return api_response.authenticate()


# -----------------------------------------------------------------------------
# Identity API exports

def set_routes(app):
    app.route('/identity',
              method='GET',
              callback=_route_versions)
    app.route('/identity/v2.0',
              method='GET',
              callback=_route_version)
    app.route('/identity/v2.0/tokens',
              method='POST',
              callback=_route_tokens)


def setup():
    pass


def teardown():
    pass
