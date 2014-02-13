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
import logging

from dwarf import api_server
from dwarf import config
from dwarf import exception
from dwarf import utils

CONF = config.Config()
LOG = logging.getLogger(__name__)


token = {
    "id": "0011223344556677",
    "expires": "2100-01-01T00:00:00-00:00",
    "tenant": {
        "id": "1000",
        "name": "dwarf-tenant"
    }
}


user = {
    "id": "1000",
    "name": "dwarf-user",
    "roles": []
}


service_compute = {
    "name": "Compute",
    "type": "compute",
    "endpoints": [{
            "tenantId": "1000",
            "publicURL": "http://127.0.0.1:%s/v1.1/1000" %
            CONF.compute_api_port,
            "region": "dwarf-region",
            "versionId": "1.1",
            "versionInfo": "http://127.0.0.1:%s/v1.1" % CONF.compute_api_port,
            "versionList": "http://127.0.0.1:%s" % CONF.compute_api_port
    }]
}


service_image = {
    "name": "Image Management",
    "type": "image",
    "endpoints": [{
            "tenantId": "1000",
            "publicURL": "http://127.0.0.1:%s/v1.0" % CONF.image_api_port,
            "region": "dwarf-region",
            "versionId": "1.0",
            "versionInfo": "http://127.0.0.1:%s/v1.0" % CONF.image_api_port,
            "versionList": "http://127.0.0.1:%s" % CONF.image_api_port
    }]
}


tokens_reply = {
    "access": {
        "token": token,
        "user": user,
        "serviceCatalog": [
            service_compute,
            service_image
        ]
    }
}


@exception.catchall
def _route_tokens():
    """
    Route:  /v2.0/tokens
    Method: POST
    """
    utils.show_request(bottle.request)

    body = json.load(bottle.request.body)
    if 'auth' in body:
        return tokens_reply


def _add_routes(app):
    """
    Add routes to the server app
    """
    app.route('/v2.0/tokens', method='POST')(_route_tokens)


@exception.catchall
def IdentityApiServer():
    """
    Instantiate and configure the API server
    """
    server = api_server.ApiServer()

    server.name = 'Identity'
    server.host = '127.0.0.1'
    server.port = CONF.identity_api_port

    server.app = bottle.Bottle()
    _add_routes(server.app)

    return server
