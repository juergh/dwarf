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

from tests import utils
from webtest import TestApp

from dwarf.image.api import ImageApiServer

IMAGE_DATA = 'Bogus image data'
IMAGE_DATA_CHUNKED = '4\r\nBogu\r\n9\r\ns image d\r\n3\r\nata\r\n0\r\n'
IMAGE_SIZE = str(len(IMAGE_DATA))
IMAGE_XSUM = 'd6beaad96c69564baec24cb194d8e146'

CREATE_IMAGE_REQ = {
    'name': 'Test image',
    'disk_format': 'raw',
    'container_format': 'bare',
    'size': IMAGE_SIZE,
}

CREATE_IMAGE_RESP = {
    'image': {
        'name': 'Test image',
        'disk_format': 'raw',
        'container_format': 'bare',
        'size': IMAGE_SIZE,

        'status': 'ACTIVE',
        'deleted': 'False',
        'checksum': IMAGE_XSUM,
        'created_at': utils.now,
        'updated_at': utils.now,
        'id': utils.uuid,
        'min_disk': '',
        'protected': 'False',
        'location': 'file:///tmp/dwarf/images/%s' % utils.uuid,
        'min_ram': '',
        'owner': '',
        'is_public': 'False',
        'deleted_at': '',
        'properties': {},
    }
}

LIST_IMAGES_RESP = {
    'images': [CREATE_IMAGE_RESP['image']]
}

SHOW_IMAGE_RESP = [
    ('Content-Length', '0'),
    ('Content-Type', 'text/html; charset=UTF-8'),

    ('x-image-meta-name', 'Test image'),
    ('x-image-meta-disk_format', 'raw'),
    ('x-image-meta-container_format', 'bare'),
    ('x-image-meta-size', IMAGE_SIZE),

    ('x-image-meta-status', 'ACTIVE'),
    ('x-image-meta-deleted', 'False'),
    ('x-image-meta-checksum', IMAGE_XSUM),
    ('x-image-meta-created_at', utils.now),
    ('x-image-meta-updated_at', utils.now),
    ('x-image-meta-id', utils.uuid),
    ('x-image-meta-min_disk', ''),
    ('x-image-meta-protected', 'False'),
    ('x-image-meta-location', 'file:///tmp/dwarf/images/%s' % utils.uuid),
    ('x-image-meta-min_ram', ''),
    ('x-image-meta-owner', ''),
    ('x-image-meta-is_public', 'False'),
    ('x-image-meta-deleted_at', ''),

    ('x-image-meta-int_id', '1'),
]

DELETE_IMAGE_RESP = [
    ('Content-Length', '0'),
    ('Content-Type', 'text/html; charset=UTF-8'),
]


LIST_VERSIONS_RESP = {
    'versions': [
        {
            'id': 'v1',
            'links': [
                {
                    'href': 'http://127.0.0.1:9292/v1/',
                    'rel': 'self',
                },
            ],
            'status': 'CURRENT',
            'updated': '2016-05-11T00:00:00Z',
        },
    ]
}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ImageApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)
        self.app.get('/v1/images/no-such-id', status=400)

    def test_create_image(self):
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        resp = self.app.post('/v1/images', IMAGE_DATA, headers, status=200)

        self.assertEqual(json.loads(resp.body), CREATE_IMAGE_RESP)
        with open('/tmp/dwarf/images/%s' % utils.uuid, 'r') as fh:
            self.assertEqual(fh.read(), IMAGE_DATA)
        # TBD: check the content of the database

    def test_create_image_chunked(self):
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        headers.append(('Transfer-Encoding', 'chunked'))
        resp = self.app.post('/v1/images', IMAGE_DATA_CHUNKED, headers,
                             status=200)

        self.assertEqual(json.loads(resp.body), CREATE_IMAGE_RESP)
        with open('/tmp/dwarf/images/%s' % utils.uuid, 'r') as fh:
            self.assertEqual(fh.read(), IMAGE_DATA)

    def test_create_image_chunked_malformed(self):
        self.app.post('/v1/images', '1', [('Transfer-Encoding', 'chunked')],
                      status=500)

    def test_list_images(self):
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        resp = self.app.get('/v1/images/detail', status=200)

        self.assertEqual(json.loads(resp.body), LIST_IMAGES_RESP)

    def test_show_image(self):
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        resp = self.app.head('/v1/images/%s' % utils.uuid, status=200)

        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()), sorted(SHOW_IMAGE_RESP))

    def test_delete_image(self):
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        resp = self.app.delete('/v1/images/%s' % utils.uuid, status=200)

        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()),
                         sorted(DELETE_IMAGE_RESP))

        self.assertEqual(os.path.exists('/tmp/dwarf/images/%s' % utils.uuid),
                         False)
        resp = self.app.get('/v1/images/detail', status=200)
        self.assertEqual(json.loads(resp.body), {'images': []})
        # TBD: check the content of the database

    def test_update_image(self):
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)

        resp = self.app.put('/v1/images/%s' % utils.uuid, status=200)
        self.assertEqual(json.loads(resp.body), CREATE_IMAGE_RESP)

    def test_list_versions(self):
        resp = self.app.get('/', status=300)
        self.assertEqual(json.loads(resp.body), LIST_VERSIONS_RESP)

        resp = self.app.get('/versions', status=200)
        self.assertEqual(json.loads(resp.body), LIST_VERSIONS_RESP)

    # -------------------------------------------------------------------------
    # Additional tests for code coverage

    def test_delete_image_cc(self):
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        os.unlink('/tmp/dwarf/images/%s' % utils.uuid)
        resp = self.app.delete('/v1/images/%s' % utils.uuid, status=200)

        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()),
                         sorted(DELETE_IMAGE_RESP))

    def test_create_image_chunked_cc(self):
        self.app.post('/v1/images', '\r', [('Transfer-Encoding', 'chunked')],
                      status=500)
        self.app.post('/v1/images', '\r1', [('Transfer-Encoding', 'chunked')],
                      status=500)
