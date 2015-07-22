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
import unittest

from dwarf import db as dwarf_db


class TestCase(unittest.TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        if os.path.exists('/tmp/dwarf'):
            shutil.rmtree('/tmp/dwarf')
        os.makedirs('/tmp/dwarf/images')
        os.makedirs('/tmp/dwarf/instances/_base')

    def tearDown(self):
        super(TestCase, self).tearDown()
        if os.path.exists('/tmp/dwarf'):
            shutil.rmtree('/tmp/dwarf')


def db_init():
    _db = dwarf_db.Controller()
    _db.delete()
    _db.init()
    return _db


def to_headers(metadata):
    headers = []
    for (key, val) in metadata.iteritems():
        if key == 'properties':
            for (k, v) in val.iteritems():
                headers.append(('x-image-meta-property-%s' % k, str(v)))
        else:
            headers.append(('x-image-meta-%s' % key, str(val)))
    return headers
