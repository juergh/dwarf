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

import json

from tests import utils
from webtest import TestApp

from dwarf import config

from dwarf.identity import api


CONF = config.Config()

REQ = {
    "auth": {
        "tenantName": "dwarf-tenant",
        "passwordCredentials": {
            "username": "dwarf-user",
            "password": "dwarf-password"
        }
    }
}

TOKEN = {
    "id": "0011223344556677",
    "expires": "2100-01-01T00:00:00-00:00",
    "tenant": {
        "id": "1000",
        "name": "dwarf-tenant"
    }
}

USER = {
    "id": "1000",
    "name": "dwarf-user",
    "roles": []
}

SERVICE_COMPUTE = {
    "name": "Compute",
    "type": "compute",
    "endpoints": [{
        "publicURL": "http://127.0.0.1:8774/v1.1/1000",
        "region": "dwarf-region",
    }]
}

SERVICE_IMAGE = {
    "name": "Image",
    "type": "image",
    "endpoints": [{
        "publicURL": "http://127.0.0.1:9292",
        "region": "dwarf-region",
    }]
}

SERVICE_IDENTITY = {
    "name": "Identity",
    "type": "identity",
    "endpoints": [{
        "publicURL": "http://127.0.0.1:35357/v2.0",
        "region": "dwarf-region",
    }]
}

TOKENS_RESPONSE = {
    "access": {
        "token": TOKEN,
        "user": USER,
        "serviceCatalog": [
            SERVICE_COMPUTE,
            SERVICE_IMAGE,
            SERVICE_IDENTITY,
        ]
    }
}

VERSION_RESPONSE = {
    "version": {
        "id": "v2.0",
        "links": [
            {
                "href": "http://%s:%s/v2.0/" % (CONF.bind_host,
                                                CONF.identity_api_port),
                "rel": "self"
            }
        ],
        "media-types": [
            {
                "base": "application/json",
                "type": "application/vnd.openstack.identity-v2.0+json"
            }
        ],
        "status": "stable",
        "updated": "2014-04-17T00:00:00Z",
    }
}

VERSIONS_RESPONSE = {
    "versions": {
        "values": [
            VERSION_RESPONSE['version']
        ]
    }
}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.server = api.IdentityApiServer()
        self.app = TestApp(self.server.app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)

    def test_api_versions(self):
        resp = self.app.get('/')
        self.assertEqual(resp.status, '300 Multiple Choices')
        self.assertEqual(json.loads(resp.body), VERSIONS_RESPONSE)

    def test_api_version(self):
        resp = self.app.get('/v2.0')
        print resp.status
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(json.loads(resp.body), VERSION_RESPONSE)

    def test_api_tokens(self):
        resp = self.app.post('/v2.0/tokens', json.dumps(REQ))
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(json.loads(resp.body), TOKENS_RESPONSE)
