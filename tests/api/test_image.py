#!/usr/bin/env python
#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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
import os

from copy import deepcopy
from webtest import TestApp

from tests import data
from tests import utils

from dwarf.image.api import ImageApiServer

CREATE_IMAGE_REQ = """{
    "container_format": "{{container_format}}",
    "disk_format": "{{disk_format}}",
    "name": "{{name}}"
}"""


def create_image_req(image):
    return utils.json_render(CREATE_IMAGE_REQ, image)


IMAGE_RESP = """{
    "checksum": "{{checksum}}",
    "container_format": "{{container_format}}",
    "created_at": "{{created_at}}",
    "disk_format": "{{disk_format}}",
    "file": "{{file}}",
    "id": "{{id}}",
    "min_disk": "{{min_disk}}",
    "min_ram": "{{min_ram}}",
    "name": "{{name}}",
    "owner": "{{owner}}",
    "protected": "{{protected}}",
    "size": "{{size}}",
    "status": "{{status}}",
    "updated_at": "{{updated_at}}",
    "visibility": "{{visibility}}"
}"""


def list_images_resp(images):
    return {'images': [utils.json_render(IMAGE_RESP, image)
                       for image in images]}


def show_image_resp(image):
    return utils.json_render(IMAGE_RESP, image)


def update_image_resp(image):
    return utils.json_render(IMAGE_RESP, image)


def create_image_resp(image):
    return utils.json_render(IMAGE_RESP, image, checksum='', file='',
                             size='', status='queued', visibility='')


VERSION_RESP = """{
    "id": "v2",
    "links": [
        {
            "href": "http://127.0.0.1:20002/v2/",
            "rel": "self"
        }
    ],
    "status": "CURRENT",
    "updated": "2016-05-11T00:00:00Z"
}"""


def list_versions_resp():
    return {'versions': [utils.json_render(VERSION_RESP)]}


image1 = data.image['11111111-2222-3333-4444-555555555555']
image2 = data.image['22222222-3333-4444-5555-666666666666']


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ImageApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)
        self.app.get('/v2/images/no-such-id', status=404)

    def test_list_versions(self):
        resp = self.app.get('/', status=300)
        self.assertEqual(json.loads(resp.body), list_versions_resp())

        resp = self.app.get('/versions', status=200)
        self.assertEqual(json.loads(resp.body), list_versions_resp())

    def test_list_images(self):
        # Preload test images
        self.create_image(image1)
        self.create_image(image2)

        resp = self.app.get('/v2/images', status=200)
        self.assertEqual(json.loads(resp.body),
                         list_images_resp([image1, image2]))

    def test_show_image(self):
        # Preload a test image
        self.create_image(image1)

        resp = self.app.get('/v2/images/%s' % image1['id'], status=200)
        self.assertEqual(json.loads(resp.body), show_image_resp(image1))

    def test_delete_image(self):
        # Preload a test image
        self.create_image(image1)

        resp = self.app.delete('/v2/images/%s' % image1['id'], status=204)
        self.assertEqual(resp.body, '')
        self.assertEqual(os.path.exists('/tmp/dwarf/images/%s' % image1['id']),
                         False)

        resp = self.app.get('/v2/images', status=200)
        self.assertEqual(json.loads(resp.body), list_images_resp([]))

    def test_update_image(self):
        # Preload a test image
        self.create_image(image1)

        key = 'name'
        val = 'Patched test image 1'

        resp = self.app.patch('/v2/images/%s' % image1['id'],
                              params=json.dumps([{'op': 'replace',
                                                  'path': '/' + key,
                                                  'value': val}]),
                              status=200)

        patched = deepcopy(image1)
        patched[key] = val
        self.assertEqual(json.loads(resp.body), update_image_resp(patched))

    def test_create_image(self):
        # Create the image in the database
        resp = self.app.post('/v2/images',
                             params=json.dumps(create_image_req(image1)),
                             status=201)
        self.assertEqual(json.loads(resp.body), create_image_resp(image1))

        # Upload the image data
        resp = self.app.put('/v2/images/%s/file' % image1['id'],
                            params=image1['data'], status=204)
        with open('/tmp/dwarf/images/%s' % image1['id'], 'r') as fh:
            self.assertEqual(fh.read(), image1['data'])

    # -------------------------------------------------------------------------
    # Additional tests for code coverage

    def test_delete_image_cc(self):
        # Preload a test image
        self.create_image(image1)
        os.unlink(image1['file'])

        resp = self.app.delete('/v2/images/%s' % image1['id'], status=204)
        self.assertEqual(resp.body, '')
