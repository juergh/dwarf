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

from webtest import TestApp

from tests import data
from tests import utils

from dwarf.compute.api import ComputeApiServer

CREATE_FLAVOR_REQ = """{
    "flavor": {
        "disk": "{{disk}}",
        "id": "{{id}}",
        "name": "{{name}}",
        "ram": "{{ram}}",
        "vcpus": "{{vcpus}}"
    }
}"""


def create_flavor_req(flavor):
    return utils.json_render(CREATE_FLAVOR_REQ, flavor)


FLAVOR_RESP = """{
% if _details:
    "disk": "{{disk}}",
    "ram": "{{ram}}",
    "vcpus": "{{vcpus}}",
% end
    "id": "{{id}}",
    "links": [
        {
            "href": "",
            "rel": "self"
        }
    ],
    "name": "{{name}}"
}"""


def list_flavors_resp(flavor, details=False):
    return {'flavors': [utils.json_render(FLAVOR_RESP, f, _details=details)
                        for f in flavor]}


def show_flavor_resp(flavor):
    return {'flavor': utils.json_render(FLAVOR_RESP, flavor, _details=True)}


def create_flavor_resp(flavor):
    return {'flavor': utils.json_render(FLAVOR_RESP, flavor, _details=True)}


flavor1 = data.flavor['100']
flavor2 = data.flavor['101']
flavor3 = data.flavor['102']


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ComputeApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_list_flavors(self):
        resp = self.app.get('/v2.0/flavors', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_flavors_resp([flavor1, flavor2, flavor3],
                                           details=False))

    def test_list_flavors_detail(self):
        resp = self.app.get('/v2.0/flavors/detail', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_flavors_resp([flavor1, flavor2, flavor3],
                                           details=True))

    def test_show_flavor(self):
        resp = self.app.get('/v2.0/flavors/%s' % flavor1['id'], status=200)
        self.assertEqual(json.loads(resp.body), show_flavor_resp(flavor1))

    def test_delete_flavor(self):
        # Delete flavor[0]
        resp = self.app.delete('/v2.0/flavors/%s' % flavor1['id'], status=200)
        self.assertEqual(resp.body, '')

        # Check the resulting list of flavors
        resp = self.app.get('/v2.0/flavors', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_flavors_resp([flavor2, flavor3], details=False))

    def test_create_flavor(self):
        # Delete flavor[0]
        self.app.delete('/v2.0/flavors/%s' % flavor1['id'], status=200)

        # Check the resulting list of flavors
        resp = self.app.get('/v2.0/flavors', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_flavors_resp([flavor2, flavor3], details=False))

        # (Re-)create flavor[0]
        resp = self.app.post('/v2.0/flavors',
                             params=json.dumps(create_flavor_req(flavor1)),
                             status=200)
        self.assertEqual(json.loads(resp.body), create_flavor_resp(flavor1))

        # Check the resulting list of flavors
        resp = self.app.get('/v2.0/flavors', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_flavors_resp([flavor2, flavor3, flavor1],
                                           details=False))
