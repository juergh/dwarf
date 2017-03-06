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
import urllib

from webtest import TestApp

from cryptography.hazmat.primitives import serialization as \
    crypto_serialization
from cryptography.hazmat.backends import default_backend as \
    crypto_default_backend
from cryptography.hazmat.primitives.asymmetric import padding as crypto_padding
from cryptography.hazmat.primitives import hashes as crypto_hashes

from tests import data
from tests import utils

from dwarf.compute.api import ComputeApiServer

KEYPAIR_REQ = """{
% if _public_key:
    "public_key": "{{public_key}}",
% end
    "name": "{{name}}"
}"""


def import_keypair_req(keypair):
    return {'keypair': utils.json_render(KEYPAIR_REQ, keypair,
                                         _public_key=True)}


def create_keypair_req(keypair):
    return {'keypair': utils.json_render(KEYPAIR_REQ, keypair,
                                         _public_key=False)}


KEYPAIR_RESP = """{
% if _details:
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "id": "{{id}}",
    "name": "{{name}}",
    "updated_at": "{{updated_at}}",
% end
% if defined('private_key'):
    "private_key": "{{private_key}}",
% end
    "fingerprint": "{{fingerprint}}",
    "name": "{{name}}",
    "public_key": "{{public_key}}"
}"""


def list_keypairs_resp(keypairs):
    return {'keypairs': [utils.json_render(KEYPAIR_RESP, k, _details=False)
                         for k in keypairs]}


def show_keypair_resp(keypair):
    return {'keypair': utils.json_render(KEYPAIR_RESP, keypair, _details=True)}


def import_keypair_resp(keypair):
    return {'keypair': utils.json_render(KEYPAIR_RESP, keypair,
                                         _details=False)}


def create_keypair_resp(keypair, **kwargs):
    return {'keypair': utils.json_render(KEYPAIR_RESP, keypair,
                                         _details=False, **kwargs)}


keypair1 = data.keypair['11111111-2222-3333-4444-555555555555']
keypair2 = data.keypair['22222222-3333-4444-5555-666666666666']


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ComputeApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_list_keypairs(self):
        # Preload test keypairs
        self.create_keypair(keypair1)
        self.create_keypair(keypair2)

        resp = self.app.get('/v2.0/os-keypairs', status=200)
        self.assertEqual(json.loads(resp.body), list_keypairs_resp([keypair1,
                                                                    keypair2]))

    def test_show_keypair(self):
        # Preload a test keypair
        self.create_keypair(keypair1)

        resp = self.app.get('/v2.0/os-keypairs/%s' %
                            urllib.quote(keypair1['name']), status=200)
        self.assertEqual(json.loads(resp.body), show_keypair_resp(keypair1))

    def test_import_keypair(self):
        resp = self.app.post('/v2.0/os-keypairs',
                             json.dumps(import_keypair_req(keypair1)),
                             status=200)
        self.assertEqual(json.loads(resp.body), import_keypair_resp(keypair1))

    def test_delete_keypair(self):
        # Preload a test keypair
        self.create_keypair(keypair1)

        # Delete the keypair
        resp = self.app.delete('/v2.0/os-keypairs/%s' %
                               urllib.quote(keypair1['name']), status=200)
        self.assertEqual(resp.body, '')

        # Check the resulting keypair list
        resp = self.app.get('/v2.0/os-keypairs', status=200)
        self.assertEqual(json.loads(resp.body), list_keypairs_resp([]))

    def test_create_keypair(self):
        resp = self.app.post('/v2.0/os-keypairs',
                             json.dumps(create_keypair_req(keypair1)),
                             status=200)
        jresp = json.loads(resp.body)

        fingerprint = jresp['keypair']['fingerprint']
        public_key = str(jresp['keypair']['public_key'])
        private_key = str(jresp['keypair']['private_key'])

        self.assertEqual(jresp, create_keypair_resp(keypair1,
                                                    fingerprint=fingerprint,
                                                    public_key=public_key,
                                                    private_key=private_key))

        # Encrypt a test message using the returned public key
        message = b'!!! test message'
        encrypted = crypto_serialization.load_ssh_public_key(
            public_key,
            backend=crypto_default_backend()
        ).encrypt(
            message,
            crypto_padding.OAEP(
                mgf=crypto_padding.MGF1(algorithm=crypto_hashes.SHA1()),
                algorithm=crypto_hashes.SHA1(),
                label=None
            )
        )

        # Decrypt the (encrypted) test message using the returned private key
        decrypted = crypto_serialization.load_pem_private_key(
            private_key,
            password=None,
            backend=crypto_default_backend()
        ).decrypt(
            encrypted,
            crypto_padding.OAEP(
                mgf=crypto_padding.MGF1(algorithm=crypto_hashes.SHA1()),
                algorithm=crypto_hashes.SHA1(),
                label=None
            )
        )

        # Verify the decrypted message
        self.assertEqual(decrypted, message)
