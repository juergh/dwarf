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

IMAGE_RESP = """{
% if _details:
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "is_public": "{{is_public}}",
    "location": "{{location}}",
    "size": "{{size}}",
    "status": "{{status}}",
    "updated_at": "{{updated_at}}",
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


def list_images_resp(images, details=False):
    return {'images': [utils.json_render(IMAGE_RESP, i, _details=details)
                       for i in images]}


def show_image_resp(image):
    return {'image': utils.json_render(IMAGE_RESP, image, _details=True)}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ComputeApiServer().app)

        # Preload test images
        self.create_image(data.image[0])
        self.create_image(data.image[1])

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_list_images(self):
        resp = self.app.get('/v2.0/1234/images', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_images_resp(data.image[0:2], details=False))

    def test_list_images_detail(self):
        resp = self.app.get('/v2.0/1234/images/detail', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_images_resp(data.image[0:2], details=True))

    def test_show_image(self):
        resp = self.app.get('/v2.0/1234/images/%s' % data.image[0]['id'],
                            status=200)
        self.assertEqual(json.loads(resp.body), show_image_resp(data.image[0]))
