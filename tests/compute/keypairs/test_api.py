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

from dwarf import db

from dwarf.compute import api

NOW = '2015-08-05 09:09:11'
UUID = '11111111-2222-3333-4444-555555555555'

KEYPAIR_ADD_NEW_REQ = {
    'keypair': {
        'name': 'Test key',
    }
}

KEYPAIR_ADD_NEW_RESP_KEYS = ('public_key', 'private_key', 'name',
                             'fingerprint')

KEYPAIR_ADD_REQ = {
    'keypair': {
        'name': 'Test key',
        'public_key': 'ssh-rsa AAAAgQC1pp5AoiINohGhl3aw1VqnFp9tfXFh17VZTVjXC'
                      'wR306c+ryaWUBR2cZuT1zlmPXnfHdkQgyRVvCke/y1eKhOT3MHjXv'
                      'jPja1OjRH17CMl2MqUKxDY3R5EJysjxvOIO1Vu2kEuDnfSTigNiVL'
                      'vii/ClShsEnayrQRbWbOEzqetbw==',
    }
}

KEYPAIR_ADD_RESP = {
    'keypair': {
        'name': 'Test key',
        'public_key': 'ssh-rsa AAAAgQC1pp5AoiINohGhl3aw1VqnFp9tfXFh17VZTVjXC'
                      'wR306c+ryaWUBR2cZuT1zlmPXnfHdkQgyRVvCke/y1eKhOT3MHjXv'
                      'jPja1OjRH17CMl2MqUKxDY3R5EJysjxvOIO1Vu2kEuDnfSTigNiVL'
                      'vii/ClShsEnayrQRbWbOEzqetbw==',
        'fingerprint': '9c:6e:3c:02:6c:98:2b:5d:60:f9:a8:ef:b0:0f:cb:76',
    }
}

KEYPAIR_LIST_RESP = {
    'keypairs': [KEYPAIR_ADD_RESP['keypair']],
}

KEYPAIR_SHOW_RESP = {
    'keypair': {
        'name': 'Test key',
        'public_key': 'ssh-rsa AAAAgQC1pp5AoiINohGhl3aw1VqnFp9tfXFh17VZTVjXC'
                      'wR306c+ryaWUBR2cZuT1zlmPXnfHdkQgyRVvCke/y1eKhOT3MHjXv'
                      'jPja1OjRH17CMl2MqUKxDY3R5EJysjxvOIO1Vu2kEuDnfSTigNiVL'
                      'vii/ClShsEnayrQRbWbOEzqetbw==',
        'fingerprint': '9c:6e:3c:02:6c:98:2b:5d:60:f9:a8:ef:b0:0f:cb:76',

        'deleted': 'False',
        'created_at': NOW,
        'updated_at': NOW,
        'deleted_at': '',
        'id': UUID,
    }
}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()

        # Mock methods
        db._now = MagicMock(return_value=NOW)   # pylint: disable=W0212
        uuid.uuid4 = MagicMock(return_value=UUID)

        self.db = utils.db_init()
        self.server = api.ComputeApiServer()
        self.app = TestApp(self.server.app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_keypair_add_new(self):
        resp = self.app.post('/v1.1/1234/os-keypairs',
                             json.dumps(KEYPAIR_ADD_NEW_REQ), status=200)
        jresp = json.loads(resp.body)

        self.assertEqual(jresp['keypair']['name'],
                         KEYPAIR_ADD_NEW_REQ['keypair']['name'])
        for key in KEYPAIR_ADD_NEW_RESP_KEYS:
            self.assertEqual(key in jresp['keypair'], True)
        for key in jresp['keypair']:
            self.assertEqual(key in KEYPAIR_ADD_NEW_RESP_KEYS, True)

    def test_keypair_add(self):
        resp = self.app.post('/v1.1/1234/os-keypairs',
                             json.dumps(KEYPAIR_ADD_REQ), status=200)

        self.assertEqual(json.loads(resp.body), KEYPAIR_ADD_RESP)

    def test_keypair_list(self):
        self.app.post('/v1.1/1234/os-keypairs', json.dumps(KEYPAIR_ADD_REQ),
                      status=200)
        resp = self.app.get('/v1.1/1234/os-keypairs', status=200)

        self.assertEqual(json.loads(resp.body), KEYPAIR_LIST_RESP)

    def test_keypair_show(self):
        self.app.post('/v1.1/1234/os-keypairs', json.dumps(KEYPAIR_ADD_REQ),
                      status=200)
        resp = self.app.get('/v1.1/1234/os-keypairs/Test%20key', status=200)

        self.assertEqual(json.loads(resp.body), KEYPAIR_SHOW_RESP)

    def test_keypair_delete(self):
        self.app.post('/v1.1/1234/os-keypairs', json.dumps(KEYPAIR_ADD_REQ),
                      status=200)
        resp = self.app.delete('/v1.1/1234/os-keypairs/Test%20key', status=200)

        self.assertEqual(resp.body, '')
        resp = self.app.get('/v1.1/1234/os-keypairs', status=200)
        self.assertEqual(json.loads(resp.body), {'keypairs': []})
