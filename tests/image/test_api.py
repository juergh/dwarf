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
import uuid

from mock import MagicMock
from tests import utils
from webtest import TestApp

from dwarf import db as dwarf_db

from dwarf.image import api

NOW = '2015-07-22 09:29:47'
UUID = '11111111-2222-3333-4444-555555555555'

IMAGE_CREATE_REQ = {
    'name': 'Test image',
    'disk_format': 'raw',
    'container_format': 'bare',
    'size': 0,
}

IMAGE_CREATE_RESP = {
    'image': {
        'name': 'Test image',
        'disk_format': 'raw',
        'container_format': 'bare',
        'size': '0',

        'status': 'ACTIVE',
        'deleted': 'False',
        'checksum': 'd41d8cd98f00b204e9800998ecf8427e',
        'created_at': '2015-07-22 09:29:47',
        'updated_at': '2015-07-22 09:29:47',
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


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()

        # Mock methods
        dwarf_db._now = MagicMock(return_value=NOW)   # pylint: disable=W0212
        uuid.uuid4 = MagicMock(return_value=UUID)

        self.db = utils.db_init()
        self.server = api.ImageApiServer()
        self.app = TestApp(self.server.app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)

    def test_image_create(self):
        headers = utils.to_headers(IMAGE_CREATE_REQ)
        resp = self.app.post('/v1/images', '', headers)
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(json.loads(resp.body), IMAGE_CREATE_RESP)
