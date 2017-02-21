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
import uuid

from mock import MagicMock
from tests import utils
from webtest import TestApp

from dwarf import db

from dwarf.compute.api import ComputeApiServer
from dwarf.image.api import ImageApiServer

NOW = '2015-07-22 09:29:47'
UUID = '11111111-2222-3333-4444-555555555555'

IMAGE_DATA = 'Bogus image data'
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

LIST_IMAGES_RESP = {
    'images': [
        {
            'id': UUID,
            'links': [{'href': '', 'rel': 'self'}],
            'name': 'Test image'
        }
    ]
}

SHOW_IMAGE_RESP = {
    "image": {
        "status": "ACTIVE",
        "name": "Test image",
        "links": [{"href": "", "rel": "self"}],
        "deleted": "False",
        "created_at": NOW,
        "updated_at": NOW,
        "location": "file:///tmp/dwarf/images/%s" % UUID,
        "is_public": "False",
        "deleted_at": "",
        "id": UUID,
        "size": IMAGE_SIZE
    }
}

LIST_IMAGES_DETAIL_RESP = {
    'images': [SHOW_IMAGE_RESP['image']]
}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()

        # Mock methods
        db._now = MagicMock(return_value=NOW)   # pylint: disable=W0212
        uuid.uuid4 = MagicMock(return_value=UUID)

        self.db = utils.db_init()
        self.server = ComputeApiServer()
        self.app = TestApp(self.server.app)

        # Preload Glance with an image
        glance = ImageApiServer()
        glance_app = TestApp(glance.app)
        headers = utils.to_headers(CREATE_IMAGE_REQ)
        glance_app.post('/v1/images', IMAGE_DATA, headers, status=200)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_list_images(self):
        resp = self.app.get('/v1.1/1234/images', status=200)
        self.assertEqual(json.loads(resp.body), LIST_IMAGES_RESP)

    def test_list_images_detail(self):
        resp = self.app.get('/v1.1/1234/images/detail', status=200)
        self.assertEqual(json.loads(resp.body), LIST_IMAGES_DETAIL_RESP)

    def test_show_image(self):
        resp = self.app.get('/v1.1/1234/images/%s' % UUID, status=200)
        self.assertEqual(json.loads(resp.body), SHOW_IMAGE_RESP)
