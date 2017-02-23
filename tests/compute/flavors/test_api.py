#!/usr/bin/env python
#
# Copyright (c) 2017 Hewlett Packard Enterprise Development, L.P.
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

from dwarf.compute.api import ComputeApiServer

LIST_FLAVORS_RESP = """{
    "flavors": [
        {
            "id": "100",
% if _details:
            "disk": "10",
            "ram": "512",
            "vcpus": "1",
% end
            "links": [
                {
                    "href": "",
                    "rel": "self"
                }
            ],
            "name": "standard.xsmall"
        },
        {
            "id": "101",
% if _details:
            "disk": "30",
            "ram": "768",
            "vcpus": "1",
% end
            "links": [
                {
                    "href": "",
                    "rel": "self"
                }
            ],
            "name": "standard.small"
        },
        {
            "id": "102",
% if _details:
            "disk": "30",
            "ram": "1024",
            "vcpus": "1",
% end
            "links": [
                {
                    "href": "",
                    "rel": "self"
                }
            ],
            "name": "standard.medium"
        }
    ]
}"""

SHOW_FLAVOR_RESP = {
    "flavor": {
        "id": "100",
        "disk": "10",
        "ram": "512",
        "vcpus": "1",
        "links": [
            {
                "href": "",
                "rel": "self"
            }
        ],
        "name": "standard.xsmall"
    }
}

CREATE_FLAVOR_REQ = {
    "flavor": {
        "disk": "20",
        "id": "999",
        "ram": "2048",
        "name": "test.flavor",
        "vcpus": "2"
    }
}

CREATE_FLAVOR_RESP = {
    "flavor": {
        "disk": "20",
        "id": "999",
        "links": [
            {
                "href": "",
                "rel": "self"
            }
        ],
        "name": "test.flavor",
        "ram": "2048",
        "vcpus": "2"
    }
}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ComputeApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_list_flavors(self):
        resp = self.app.get('/v1.1/1234/flavors', status=200)
        self.assertEqual(json.loads(resp.body),
                         utils.json_render(LIST_FLAVORS_RESP, _details=False))

    def test_list_flavors_details(self):
        resp = self.app.get('/v1.1/1234/flavors/detail', status=200)
        self.assertEqual(json.loads(resp.body),
                         utils.json_render(LIST_FLAVORS_RESP, _details=True))

    def test_show_flavor(self):
        resp = self.app.get('/v1.1/1234/flavors/100', status=200)
        self.assertEqual(json.loads(resp.body), SHOW_FLAVOR_RESP)

    def test_create_flavor(self):
        resp = self.app.post('/v1.1/1234/flavors',
                             json.dumps(CREATE_FLAVOR_REQ), status=200)
        self.assertEqual(json.loads(resp.body), CREATE_FLAVOR_RESP)

        flist = utils.json_render(LIST_FLAVORS_RESP, _details=True)
        flist['flavors'].append(CREATE_FLAVOR_RESP['flavor'])

        resp = self.app.get('/v1.1/1234/flavors/detail', status=200)
        self.assertEqual(json.loads(resp.body), flist)

    def test_delete_flavor(self):
        resp = self.app.delete('/v1.1/1234/flavors/100', status=200)
        self.assertEqual(resp.body, '')

        flist = utils.json_render(LIST_FLAVORS_RESP, _details=False)
        flist['flavors'].pop(0)

        resp = self.app.get('/v1.1/1234/flavors', status=200)
        self.assertEqual(json.loads(resp.body), flist)
