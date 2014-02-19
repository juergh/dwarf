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
import mock
import unittest

from StringIO import StringIO
from webtest import TestApp

from dwarf.identity import api
from dwarf import exception

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
            "tenantId": "1000",
            "publicURL": "http://127.0.0.1:8774/v1.1/1000",
            "region": "dwarf-region",
            "versionId": "1.1",
            "versionInfo": "http://127.0.0.1:8774/v1.1",
            "versionList": "http://127.0.0.1:8774"
    }]
}

SERVICE_IMAGE = {
    "name": "Image Management",
    "type": "image",
    "endpoints": [{
            "tenantId": "1000",
            "publicURL": "http://127.0.0.1:9292/v1.0",
            "region": "dwarf-region",
            "versionId": "1.0",
            "versionInfo": "http://127.0.0.1:9292/v1.0",
            "versionList": "http://127.0.0.1:9292"
    }]
}

TOKENS_RESPONSE = {
    "access": {
        "token": TOKEN,
        "user": USER,
        "serviceCatalog": [
            SERVICE_COMPUTE,
            SERVICE_IMAGE
        ]
    }
}


class ApiTestCase(unittest.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()

    def tearDown(self):
        super(ApiTestCase, self).setUp()

    def mock_request(self, request, headers, body):
        request.headers = headers
        request.body = body

#    @mock.patch('bottle.request')
#    def test_api_routes(self, request):
#        self.mock_request(request, headers={}, body=StringIO(json.dumps(REQ)))
#        resp = api._route_tokens()
#        self.assertTrue('access' in resp)
#        self.assertTrue('token' in resp['access'])
#        self.assertTrue('user' in resp['access'])
#        self.assertTrue('serviceCatalog' in resp['access'])

    @mock.patch('bottle.request')
    def test_http_error(self, request):
        self.mock_request(request, None, None)
        self.assertRaises(bottle.HTTPError, api._route_tokens)

    def test_api_server(self):
        server = api.IdentityApiServer()
        app = TestApp(server.app)
        resp = app.post('/v2.0/tokens', json.dumps(REQ))
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(json.loads(resp.body), TOKENS_RESPONSE)
