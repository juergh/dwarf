#!/usr/bin/python

from __future__ import print_function

from base64 import b64encode
from hashlib import md5
from M2Crypto import RSA

from dwarf import db


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self):
        """
        List all keypairs
        """
        print('compute.keypairs.list()')
        keypairs = self.db.keypairs.list()

        # Remove the IDs from the keypairs to not confuse the Nova CLI
        for keypair in keypairs:
            del keypair['id']

        return keypairs

    def add(self, keypair):
        """
        Add a keypair
        """
        print('compute.keypairs.add()')

        # Generate a new keypair if the request doesn't contain a public key
        if 'public_key' not in keypair:
            key = RSA.gen_key(1024, 65537, callback=lambda: None)
            keypair['public_key'] = 'ssh-rsa %s' % b64encode(key.pub()[1])
            keypair['private_key'] = key.as_pem(cipher=None)

        # Calculate the key fingerprint
        fp_plain = md5(b64encode(key.pub()[1])).hexdigest()
        fp = ':'.join(a + b for (a, b) in zip(fp_plain[::2], fp_plain[1::2]))

        # Add the keypair to the database
        # TODO: calculate fingerprint
        self.db.keypairs.add(name=keypair['name'],
                             fingerprint=fp,
                             public_key=keypair['public_key'])

        # TODO: fix user_id
        keypair['user_id'] = 1000

        return keypair

    def delete(self, *args, **_kwargs):
        """
        Delete a keypair
        """
        print('compute.keypairs.delete()')
        name = args[0]
        self.db.keypairs.delete(name=name)
