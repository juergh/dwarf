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

# import time
import json

from webtest import TestApp

from tests import data
from tests import utils

from dwarf.api_server import ApiServer

SERVER_REQ = """{
    "flavorRef": "{{flavor_id}}",
    "imageRef": "{{image_id}}",
    "name": "{{name}}"
}"""


def create_server_req(server):
    return {'server': utils.json_render(SERVER_REQ, server)}


SERVER_RESP = """{
    "server": {
        "addresses": {
            "private": [
                {
                    "addr": "{{ip}}",
                    "version": "4"
                }
            ]
        },
        "config_drive": "False",
        "created_at": "2001-02-03 04:05:06",
        "deleted": "False",
        "deleted_at": "",
        "flavor": {
            "id": "100",
            "links": [
                {
                    "href": "",
                    "rel": "self"
                }
            ]
        },
        "id": "11111111-2222-3333-4444-555555555555",
        "image": {
            "id": "11111111-2222-3333-4444-555555555555",
            "links": [
                {
                    "href": "",
                    "rel": "self"
                }
            ]
        },
        "key_name": "None",
        "name": "Test server 1",
        "status": "building",
        "updated_at": "2001-02-03 04:05:06"
    }
}"""


image1 = data.image['11111111-2222-3333-4444-555555555555']
server1 = data.server['11111111-2222-3333-4444-555555555555']


class DwarfTestCase(utils.TestCase):

    def setUp(self):
        super(DwarfTestCase, self).setUp()
        self.app = TestApp(ApiServer().app)

    # Commented out to silence pylint
    # def tearDown(self):
    #     super(DwarfTestCase, self).tearDown()

    def test_create_server_no_image(self):
        self.app.post('/compute/v2.0/servers',
                      params=json.dumps(create_server_req(server1)),
                      status=404)

    def test_create_server(self):
        # Preload a test image
        self.create_image(image1)

        resp = self.app.post('/compute/v2.0/servers',
                             params=json.dumps(create_server_req(server1)),
                             status=200)
        self.assertEqual(json.loads(resp.body),
                         utils.json_render(SERVER_RESP, ip=''))
