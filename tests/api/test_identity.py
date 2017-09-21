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

from webtest import TestApp

from tests import utils

from dwarf.api_server import ApiServer

AUTH_REQ = {
    "auth": {
        "tenantName": "dwarf-tenant",
        "passwordCredentials": {
            "username": "dwarf-user",
            "password": "dwarf-password"
        }
    }
}


def auth_req():
    return AUTH_REQ


AUTH_RESP = {
    "access": {
        "token": {
            "id": "0011223344556677",
            "expires": "2100-01-01T00:00:00-00:00",
            "tenant": {
                "id": "1000",
                "name": "dwarf-tenant"
            }
        },
        "user": {
            "id": "1000",
            "name": "dwarf-user",
            "roles": []
        },
        "serviceCatalog": [
            {
                "name": "Compute",
                "type": "compute",
                "endpoints": [
                    {
                        "publicURL": "http://127.0.0.1:20000/compute/v2.0",
                        "region": "dwarf-region"
                    }
                ]
            },
            {
                "name": "Image",
                "type": "image",
                "endpoints": [
                    {
                        "publicURL": "http://127.0.0.1:20000/image",
                        "region": "dwarf-region"
                    }
                ]
            },
            {
                "name": "Identity",
                "type": "identity",
                "endpoints": [
                    {
                        "publicURL": "http://127.0.0.1:20000/identity",
                        "region": "dwarf-region"
                    }
                ]
            }
        ]
    }
}


def auth_resp():
    return AUTH_RESP


VERSION_RESP = {
    "id": "v2.0",
    "links": [
        {
            "href": "http://127.0.0.1:20000/identity/v2.0/",
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
    "updated": "2014-04-17T00:00:00Z"
}


def show_version_resp():
    return {'version': VERSION_RESP}


def list_versions_resp():
    return {'versions': {'values': [VERSION_RESP]}}


class DwarfTestCase(utils.TestCase):

    def setUp(self):
        super(DwarfTestCase, self).setUp()
        self.app = TestApp(ApiServer().app)

    # Commented out to silence pylint
    # def tearDown(self):
    #     super(DwarfTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)

    def test_list_versions(self):
        resp = self.app.get('/identity', status=300)
        self.assertEqual(json.loads(resp.body), list_versions_resp())

    def test_show_version(self):
        resp = self.app.get('/identity/v2.0', status=200)
        self.assertEqual(json.loads(resp.body), show_version_resp())

    def test_authenticate(self):
        resp = self.app.post('/identity/v2.0/tokens',
                             params=json.dumps(auth_req()), status=200)
        self.assertEqual(json.loads(resp.body), auth_resp())
