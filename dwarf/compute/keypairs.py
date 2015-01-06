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

from base64 import b64encode, b64decode
from hashlib import md5
from M2Crypto import RSA   # pylint: disable=F0401

from dwarf import db
from dwarf import utils

LOG = logging.getLogger(__name__)

KEYPAIRS_INFO = ('fingerprint', 'name', 'public_key')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self):
        """
        List all keypairs
        """
        LOG.info('list()')

        keypairs = self.db.keypairs.list()
        return utils.sanitize(keypairs, KEYPAIRS_INFO)

    def add(self, keypair):
        """
        Add a keypair
        """
        LOG.info('add(keypair=%s)', keypair)

        # Generate a new keypair if the request doesn't contain a public key
        if 'public_key' in keypair:
            public_key = keypair['public_key']
            private_key = None
        else:
            key = RSA.gen_key(1024, 65537, callback=lambda: None)
            public_key = 'ssh-rsa %s' % b64encode(key.pub()[1])
            private_key = key.as_pem(cipher=None)

        # Calculate the key fingerprint
        fp_plain = md5(b64decode(public_key.split()[1])).hexdigest()
        fp = ':'.join(a + b for (a, b) in zip(fp_plain[::2], fp_plain[1::2]))

        # Create the new keypair in the database
        new_keypair = self.db.keypairs.create(name=keypair['name'],
                                              fingerprint=fp,
                                              public_key=public_key)

        if private_key is None:
            return utils.sanitize(new_keypair, KEYPAIRS_INFO)

        new_keypair['private_key'] = private_key
        return utils.sanitize(new_keypair, KEYPAIRS_INFO + ('private_key', ))

    def delete(self, keypair_name):
        """
        Delete a keypair
        """
        LOG.info('delete(name=%s)', keypair_name)

        self.db.keypairs.delete(name=keypair_name)

    def exists(self, keypair_name):
        """
        Check if a keypair exists
        """
        LOG.info('exists(name=%s)', keypair_name)
        self.db.keypairs.show(name=keypair_name)
