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

from tests import utils
from webtest import TestApp

from cryptography.hazmat.primitives import serialization as \
    crypto_serialization
from cryptography.hazmat.backends import default_backend as \
    crypto_default_backend
from cryptography.hazmat.primitives.asymmetric import padding as crypto_padding
from cryptography.hazmat.primitives import hashes as crypto_hashes

from dwarf.compute.api import ComputeApiServer

ADD_NEW_KEYPAIR_REQ = {
    'keypair': {
        'name': 'Test key',
    }
}

ADD_NEW_KEYPAIR_RESP_KEYS = ('public_key', 'private_key', 'name',
                             'fingerprint')

ADD_KEYPAIR_REQ = {
    'keypair': {
        'name': 'Test key',
        'public_key': 'ssh-rsa AAAAgQC1pp5AoiINohGhl3aw1VqnFp9tfXFh17VZTVjXC'
                      'wR306c+ryaWUBR2cZuT1zlmPXnfHdkQgyRVvCke/y1eKhOT3MHjXv'
                      'jPja1OjRH17CMl2MqUKxDY3R5EJysjxvOIO1Vu2kEuDnfSTigNiVL'
                      'vii/ClShsEnayrQRbWbOEzqetbw==',
    }
}

ADD_KEYPAIR_RESP = {
    'keypair': {
        'name': 'Test key',
        'public_key': 'ssh-rsa AAAAgQC1pp5AoiINohGhl3aw1VqnFp9tfXFh17VZTVjXC'
                      'wR306c+ryaWUBR2cZuT1zlmPXnfHdkQgyRVvCke/y1eKhOT3MHjXv'
                      'jPja1OjRH17CMl2MqUKxDY3R5EJysjxvOIO1Vu2kEuDnfSTigNiVL'
                      'vii/ClShsEnayrQRbWbOEzqetbw==',
        'fingerprint': '9c:6e:3c:02:6c:98:2b:5d:60:f9:a8:ef:b0:0f:cb:76',
    }
}

LIST_KEYPAIRS_RESP = {
    'keypairs': [ADD_KEYPAIR_RESP['keypair']],
}

SHOW_KEYPAIR_RESP = {
    'keypair': {
        'name': 'Test key',
        'public_key': 'ssh-rsa AAAAgQC1pp5AoiINohGhl3aw1VqnFp9tfXFh17VZTVjXC'
                      'wR306c+ryaWUBR2cZuT1zlmPXnfHdkQgyRVvCke/y1eKhOT3MHjXv'
                      'jPja1OjRH17CMl2MqUKxDY3R5EJysjxvOIO1Vu2kEuDnfSTigNiVL'
                      'vii/ClShsEnayrQRbWbOEzqetbw==',
        'fingerprint': '9c:6e:3c:02:6c:98:2b:5d:60:f9:a8:ef:b0:0f:cb:76',

        'deleted': 'False',
        'created_at': utils.now,
        'updated_at': utils.now,
        'deleted_at': '',
        'id': utils.uuid,
    }
}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ComputeApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_add_new_keypair(self):
        resp = self.app.post('/v1.1/1234/os-keypairs',
                             json.dumps(ADD_NEW_KEYPAIR_REQ), status=200)
        jresp = json.loads(resp.body)

        self.assertEqual(jresp['keypair']['name'],
                         ADD_NEW_KEYPAIR_REQ['keypair']['name'])
        for key in ADD_NEW_KEYPAIR_RESP_KEYS:
            self.assertEqual(key in jresp['keypair'], True)
        for key in jresp['keypair']:
            self.assertEqual(key in ADD_NEW_KEYPAIR_RESP_KEYS, True)

        # Verify the returned keypair
        private_key = crypto_serialization.load_pem_private_key(
            str(jresp['keypair']['private_key']),
            password=None,
            backend=crypto_default_backend()
        )
        public_key = crypto_serialization.load_ssh_public_key(
            str(jresp['keypair']['public_key']),
            backend=crypto_default_backend()
        )
        message = b'!!! test message'
        ciphertext = public_key.encrypt(
            message,
            crypto_padding.OAEP(
                mgf=crypto_padding.MGF1(algorithm=crypto_hashes.SHA1()),
                algorithm=crypto_hashes.SHA1(),
                label=None
            )
        )
        plaintext = private_key.decrypt(
            ciphertext,
            crypto_padding.OAEP(
                mgf=crypto_padding.MGF1(algorithm=crypto_hashes.SHA1()),
                algorithm=crypto_hashes.SHA1(),
                label=None
            )
        )
        self.assertEqual(message, plaintext)

    def test_add_keypair(self):
        resp = self.app.post('/v1.1/1234/os-keypairs',
                             json.dumps(ADD_KEYPAIR_REQ), status=200)

        self.assertEqual(json.loads(resp.body), ADD_KEYPAIR_RESP)

    def test_list_keypairs(self):
        self.app.post('/v1.1/1234/os-keypairs', json.dumps(ADD_KEYPAIR_REQ),
                      status=200)
        resp = self.app.get('/v1.1/1234/os-keypairs', status=200)

        self.assertEqual(json.loads(resp.body), LIST_KEYPAIRS_RESP)

    def test_show_keypair(self):
        self.app.post('/v1.1/1234/os-keypairs', json.dumps(ADD_KEYPAIR_REQ),
                      status=200)
        resp = self.app.get('/v1.1/1234/os-keypairs/Test%20key', status=200)

        self.assertEqual(json.loads(resp.body), SHOW_KEYPAIR_RESP)

    def test_delete_keypair(self):
        self.app.post('/v1.1/1234/os-keypairs', json.dumps(ADD_KEYPAIR_REQ),
                      status=200)
        resp = self.app.delete('/v1.1/1234/os-keypairs/Test%20key', status=200)

        self.assertEqual(resp.body, '')
        resp = self.app.get('/v1.1/1234/os-keypairs', status=200)
        self.assertEqual(json.loads(resp.body), {'keypairs': []})
