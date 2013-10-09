#!/usr/bin/python

from __future__ import print_function

import logging

from base64 import b64encode, b64decode
from hashlib import md5
from M2Crypto import RSA

from dwarf import db
from dwarf.common import utils

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

        # Add the keypair to the database
        new_keypair = self.db.keypairs.add(name=keypair['name'],
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
