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


import os
import shutil
import StringIO
import unittest
import uuid

from copy import deepcopy

from tests import data

from dwarf import db
from dwarf import utils

from dwarf.compute import keypairs
from dwarf.image import images

json_render = utils.json_render


class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None
        self.db = None
        self.uuid_idx = 0

    def now(self):
        return data.now

    def uuid(self):
        resp = data.uuid[self.uuid_idx]
        self.uuid_idx += 1
        return resp

    def create_image(self, image):
        self.uuid_idx = int(image['int_id']) - 1

        cp_image = deepcopy(image)
        images.Controller().create(StringIO.StringIO(cp_image['data']),
                                   cp_image)

    def create_keypair(self, keypair):
        self.uuid_idx = int(keypair['int_id']) - 1

        cp_keypair = deepcopy(keypair)
        keypairs.Controller().create(cp_keypair)

    def setUp(self):
        super(TestCase, self).setUp()

        # Reset the UUID array index
        self.uuid_idx = 0

        # Default mocks
        db._now = self.now   # pylint: disable=W0212
        uuid.uuid4 = self.uuid

        # Create the temp directory tree
        if os.path.exists('/tmp/dwarf'):
            shutil.rmtree('/tmp/dwarf')
        os.makedirs('/tmp/dwarf/images')
        os.makedirs('/tmp/dwarf/instances/_base')

        # Initialize the database
        self.db = db.Controller()
        self.db.init()

    def tearDown(self):
        super(TestCase, self).tearDown()

        # Purge the temp directory tree
        if os.path.exists('/tmp/dwarf'):
            shutil.rmtree('/tmp/dwarf')


def to_headers(metadata):
    headers = []
    for (key, val) in metadata.iteritems():
        if key == 'properties':
            for (k, v) in val.iteritems():
                headers.append(('x-image-meta-property-%s' % k, str(v)))
        else:
            headers.append(('x-image-meta-%s' % key, str(val)))
    return headers
