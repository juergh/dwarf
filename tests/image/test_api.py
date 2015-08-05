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
import uuid

from mock import MagicMock
from tests import utils
from webtest import TestApp

from dwarf import db

from dwarf.image import api

NOW = '2015-07-22 09:29:47'
UUID = '11111111-2222-3333-4444-555555555555'

IMAGE_DATA = 'Bogus image data'
IMAGE_DATA_CHUNKED = '4\r\nBogu\r\n9\r\ns image d\r\n3\r\nata\r\n0\r\n'
IMAGE_SIZE = str(len(IMAGE_DATA))
IMAGE_XSUM = 'd6beaad96c69564baec24cb194d8e146'

IMAGE_CREATE_REQ = {
    'name': 'Test image',
    'disk_format': 'raw',
    'container_format': 'bare',
    'size': IMAGE_SIZE,
}

IMAGE_CREATE_RESP = {
    'image': {
        'name': 'Test image',
        'disk_format': 'raw',
        'container_format': 'bare',
        'size': IMAGE_SIZE,

        'status': 'ACTIVE',
        'deleted': 'False',
        'checksum': IMAGE_XSUM,
        'created_at': NOW,
        'updated_at': NOW,
        'id': UUID,
        'min_disk': '',
        'protected': 'False',
        'location': 'file:///tmp/dwarf/images/%s' % UUID,
        'min_ram': '',
        'owner': '',
        'is_public': 'False',
        'deleted_at': '',
        'properties': {},
    }
}

IMAGE_LIST_RESP = {
    'images': [IMAGE_CREATE_RESP['image']]
}

IMAGE_SHOW_RESP = [
    ('Content-Length', '0'),
    ('Content-Type', 'text/html; charset=UTF-8'),

    ('x-image-meta-name', 'Test image'),
    ('x-image-meta-disk_format', 'raw'),
    ('x-image-meta-container_format', 'bare'),
    ('x-image-meta-size', IMAGE_SIZE),

    ('x-image-meta-status', 'ACTIVE'),
    ('x-image-meta-deleted', 'False'),
    ('x-image-meta-checksum', IMAGE_XSUM),
    ('x-image-meta-created_at', NOW),
    ('x-image-meta-updated_at', NOW),
    ('x-image-meta-id', UUID),
    ('x-image-meta-min_disk', ''),
    ('x-image-meta-protected', 'False'),
    ('x-image-meta-location', 'file:///tmp/dwarf/images/%s' % UUID),
    ('x-image-meta-min_ram', ''),
    ('x-image-meta-owner', ''),
    ('x-image-meta-is_public', 'False'),
    ('x-image-meta-deleted_at', ''),

    ('x-image-meta-int_id', '1'),
]

IMAGE_DELETE_RESP = [
    ('Content-Length', '0'),
    ('Content-Type', 'text/html; charset=UTF-8'),
]


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()

        # Mock methods
        db._now = MagicMock(return_value=NOW)   # pylint: disable=W0212
        uuid.uuid4 = MagicMock(return_value=UUID)

        self.db = utils.db_init()
        self.server = api.ImageApiServer()
        self.app = TestApp(self.server.app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)
        self.app.get('/v1/images/no-such-id', status=400)

    def test_image_create(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        resp = self.app.post('/v1/images', IMAGE_DATA, headers, status=200)

        self.assertEqual(json.loads(resp.body), IMAGE_CREATE_RESP)
        with open('/tmp/dwarf/images/%s' % UUID, 'r') as fh:
            self.assertEqual(fh.read(), IMAGE_DATA)
        # TBD: check the content of the database

    def test_image_create_chunked(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        headers.append(('Transfer-Encoding', 'chunked'))
        resp = self.app.post('/v1/images', IMAGE_DATA_CHUNKED, headers,
                             status=200)

        self.assertEqual(json.loads(resp.body), IMAGE_CREATE_RESP)
        with open('/tmp/dwarf/images/%s' % UUID, 'r') as fh:
            self.assertEqual(fh.read(), IMAGE_DATA)

    def test_image_create_chunked_malformed(self):
        self.app.post('/v1/images', '1', [('Transfer-Encoding', 'chunked')],
                      status=500)

    def test_image_create_chunked_cc(self):
        self.app.post('/v1/images', '\r', [('Transfer-Encoding', 'chunked')],
                      status=500)
        self.app.post('/v1/images', '\r1', [('Transfer-Encoding', 'chunked')],
                      status=500)

    def test_image_list(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        resp = self.app.get('/v1/images/detail', status=200)

        self.assertEqual(json.loads(resp.body), IMAGE_LIST_RESP)

    def test_image_show(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        resp = self.app.head('/v1/images/%s' % UUID, status=200)

        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()), sorted(IMAGE_SHOW_RESP))

    def test_image_delete(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        resp = self.app.delete('/v1/images/%s' % UUID, status=200)

        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()),
                         sorted(IMAGE_DELETE_RESP))

        self.assertEqual(os.path.exists('/tmp/dwarf/images/%s' % UUID), False)
        resp = self.app.get('/v1/images/detail', status=200)
        self.assertEqual(json.loads(resp.body), {'images': []})
        # TBD: check the content of the database

    def test_image_update(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)

        resp = self.app.put('/v1/images/%s' % UUID, status=200)
        self.assertEqual(json.loads(resp.body), IMAGE_CREATE_RESP)

    # -------------------------------------------------------------------------
    # Additional tests for code coverage

    def test_image_delete_cc(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        self.app.post('/v1/images', IMAGE_DATA, headers, status=200)
        os.unlink('/tmp/dwarf/images/%s' % UUID)
        resp = self.app.delete('/v1/images/%s' % UUID, status=200)

        self.assertEqual(resp.body, '')
        self.assertEqual(sorted(resp.headers.items()),
                         sorted(IMAGE_DELETE_RESP))
