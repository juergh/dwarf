#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
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

from __future__ import print_function

import logging

from base64 import b64decode
from cryptography.hazmat.primitives import serialization as \
    crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa as crypto_rsa
from cryptography.hazmat.backends import default_backend as \
    crypto_default_backend
from hashlib import md5

from dwarf import db

LOG = logging.getLogger(__name__)

KEYPAIRS_INFO = ('fingerprint', 'name', 'public_key')
KEYPAIRS_DETAIL = ('created_at', 'fingerprint', 'name', 'public_key')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def create(self, keypair):
        """
        create (or import) a keypair
        """
        LOG.info('create(keypair=%s)', keypair)

        # Generate a new keypair if the request doesn't contain a public key
        if 'public_key' in keypair:
            public_key = keypair['public_key']
            private_key = None
        else:
            key = crypto_rsa.generate_private_key(
                backend=crypto_default_backend(),
                public_exponent=65537,
                key_size=2048,
            )
            private_key = key.private_bytes(
                crypto_serialization.Encoding.PEM,
                crypto_serialization.PrivateFormat.PKCS8,
                crypto_serialization.NoEncryption(),
            )
            public_key = key.public_key().public_bytes(
                crypto_serialization.Encoding.OpenSSH,
                crypto_serialization.PublicFormat.OpenSSH,
            )

        # Calculate the key fingerprint
        fp_plain = md5(b64decode(public_key.split()[1])).hexdigest()
        fp = ':'.join(a + b for (a, b) in zip(fp_plain[::2], fp_plain[1::2]))

        # Create the new keypair in the database
        new_keypair = self.db.keypairs.create(name=keypair['name'],
                                              fingerprint=fp,
                                              public_key=public_key)

        # Add the private key to the response
        if private_key is not None:
            new_keypair['private_key'] = private_key

        return new_keypair

    def delete(self, keypair_name):
        """
        Delete a keypair
        """
        LOG.info('delete(name=%s)', keypair_name)
        return self.db.keypairs.delete(name=keypair_name)

    def list(self):
        """
        List all keypairs
        """
        LOG.info('list()')
        return self.db.keypairs.list()

    def show(self, keypair_name):
        """
        Show keypair details
        """
        LOG.info('show(name=%s)', keypair_name)
        return self.db.keypairs.show(name=keypair_name)
