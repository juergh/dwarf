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

from webtest import TestApp

from tests import data
from tests import utils

from dwarf.image.api import ImageApiServer


DELETE_IMAGE_RESP = """[
    ["Content-Length", "0"],
    ["Content-Type", "text/html; charset=UTF-8"]
]"""


def delete_image_resp(image):
    return [(e[0], e[1]) for e in utils.json_render(DELETE_IMAGE_RESP, image)]


CREATE_IMAGE_REQ = """{
    "container_format": "{{container_format}}",
    "disk_format": "{{disk_format}}",
    "name": "{{name}}",
    "size": "{{size}}"
}"""


def create_image_req(image):
    return utils.json_render(CREATE_IMAGE_REQ, image)


SHOW_IMAGE_RESP = """[
    ["Content-Length", "0"],
    ["Content-Type", "text/html; charset=UTF-8"],

    ["x-image-meta-checksum", "{{checksum}}"],
    ["x-image-meta-container_format", "{{container_format}}"],
    ["x-image-meta-created_at", "{{created_at}}"],
    ["x-image-meta-deleted", "{{deleted}}"],
    ["x-image-meta-deleted_at", "{{deleted_at}}"],
    ["x-image-meta-disk_format", "{{disk_format}}"],
    ["x-image-meta-id", "{{id}}"],
    ["x-image-meta-is_public", "{{is_public}}"],
    ["x-image-meta-int_id", "{{int_id}}"],
    ["x-image-meta-location", "{{location}}"],
    ["x-image-meta-min_disk", "{{min_disk}}"],
    ["x-image-meta-min_ram", "{{min_ram}}"],
    ["x-image-meta-name", "{{name}}"],
    ["x-image-meta-owner", "{{owner}}"],
    ["x-image-meta-protected", "{{protected}}"],
    ["x-image-meta-size", "{{size}}"],
    ["x-image-meta-status", "{{status}}"],
    ["x-image-meta-updated_at", "{{updated_at}}"]
]"""


def show_image_resp(image):
    return [(e[0], e[1]) for e in utils.json_render(SHOW_IMAGE_RESP, image)]


IMAGE_RESP = """{
    "checksum": "{{checksum}}",
    "container_format": "{{container_format}}",
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "disk_format": "{{disk_format}}",
    "id": "{{id}}",
    "is_public": "{{is_public}}",
    "location": "{{location}}",
    "min_disk": "{{min_disk}}",
    "min_ram": "{{min_ram}}",
    "name": "{{name}}",
    "owner": "{{owner}}",
    "properties": {{properties}},
    "protected": "{{protected}}",
    "size": "{{size}}",
    "status": "{{status}}",
    "updated_at": "{{updated_at}}"
}"""


def list_images_resp(images):
    return {'images': [utils.json_render(IMAGE_RESP, image)
                       for image in images]}


def create_image_resp(image):
    return {'image': utils.json_render(IMAGE_RESP, image)}


VERSION_RESP = """{
    "id": "v1",
    "links": [
        {
            "href": "http://127.0.0.1:9292/v1/",
            "rel": "self"
        }
    ],
    "status": "CURRENT",
    "updated": "2016-05-11T00:00:00Z"
}"""


def list_versions_resp():
    return {'versions': [utils.json_render(VERSION_RESP)]}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ImageApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)
        self.app.get('/v1/images/no-such-id', status=400)

    def test_list_versions(self):
        resp = self.app.get('/', status=300)
        self.assertEqual(json.loads(resp.body), list_versions_resp())

        resp = self.app.get('/versions', status=200)
        self.assertEqual(json.loads(resp.body), list_versions_resp())

    def test_list_images(self):
        # Preload test images
        test_images = data.image[0:2]
        for test_image in test_images:
            self.create_image(test_image)

        resp = self.app.get('/v1/images/detail', status=200)
        self.assertEqual(json.loads(resp.body), list_images_resp(test_images))

    def test_create_image(self):
        test_image = data.image[0]
        headers = utils.to_headers(create_image_req(test_image))

        resp = self.app.post('/v1/images', test_image['data'], headers,
                             status=200)
        self.assertEqual(json.loads(resp.body), create_image_resp(test_image))
        with open('/tmp/dwarf/images/%s' % test_image['id'], 'r') as fh:
            self.assertEqual(fh.read(), test_image['data'])

    def test_create_image_chunked(self):
        test_image = data.image[0]
        headers = utils.to_headers(create_image_req(test_image))
        headers.append(('Transfer-Encoding', 'chunked'))

        resp = self.app.post('/v1/images', test_image['data_chunked'], headers,
                             status=200)
        self.assertEqual(json.loads(resp.body), create_image_resp(test_image))
        with open('/tmp/dwarf/images/%s' % test_image['id'], 'r') as fh:
            self.assertEqual(fh.read(), test_image['data'])

    def test_create_image_chunked_malformed(self):
        self.app.post('/v1/images', 'foo', [('Transfer-Encoding', 'chunked')],
                      status=500)

    def test_show_image(self):
        # Preload a test image
        test_image = data.image[0]
        self.create_image(test_image)

        resp = self.app.head('/v1/images/%s' % test_image['id'], status=200)
        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()),
                         sorted(show_image_resp(test_image)))

    def test_delete_image(self):
        # Preload a test image
        test_image = data.image[0]
        self.create_image(test_image)

        resp = self.app.delete('/v1/images/%s' % test_image['id'], status=200)
        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()),
                         sorted(delete_image_resp(test_image)))
        self.assertEqual(os.path.exists('/tmp/dwarf/images/%s' %
                                        test_image['id']), False)

        resp = self.app.get('/v1/images/detail', status=200)
        self.assertEqual(json.loads(resp.body), {'images': []})

    def test_update_image(self):
        # Preload a test image
        test_image = data.image[0]
        self.create_image(test_image)

        resp = self.app.put('/v1/images/%s' % test_image['id'], status=200)
        self.assertEqual(json.loads(resp.body), create_image_resp(test_image))

    # -------------------------------------------------------------------------
    # Additional tests for code coverage

    def test_delete_image_cc(self):
        # Preload a test image
        test_image = data.image[0]
        self.create_image(test_image)
        os.unlink('/tmp/dwarf/images/%s' % test_image['id'])

        resp = self.app.delete('/v1/images/%s' % test_image['id'], status=200)
        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()),
                         sorted(delete_image_resp(test_image)))

    def test_create_image_chunked_cc(self):
        self.app.post('/v1/images', '\r', [('Transfer-Encoding', 'chunked')],
                      status=500)
        self.app.post('/v1/images', '\r1', [('Transfer-Encoding', 'chunked')],
                      status=500)
