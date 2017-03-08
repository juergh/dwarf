#!/usr/bin/env python
#
# Copyright (c) 2017 Hewlett Packard Enterprise, L.P.
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

import os

from tests import data
from tests import utils


def verify_private_key(stdout):
    line = [l for l in stdout.split('\n') if l != '']
    if ((line[0] == '-----BEGIN PRIVATE KEY-----' and
         line[-1] == '-----END PRIVATE KEY-----')):
        return stdout
    return ''


def cwd(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


image1 = data.image['11111111-2222-3333-4444-555555555555']


class ClientTestCase(utils.TestCase):

    def setUp(self):
        super(ClientTestCase, self).setUp()
        self.start_dwarf()

    def tearDown(self):
        self.stop_dwarf()
        super(ClientTestCase, self).tearDown()

    def test_nova_flavors(self):
        self.exec_verify(['nova', 'flavor-list'],
                         filename=cwd('nova_flavor-list'))

        self.exec_verify(['nova', 'flavor-show', '100'],
                         filename=cwd('nova_flavor-show'))

        self.exec_verify(['nova', 'flavor-delete', '100'],
                         filename=cwd('nova_flavor-delete'))

        self.exec_verify(['nova', 'flavor-create', 'test.flavor', '999',
                          '1024', '15', '2'],
                         filename=cwd('nova_flavor-create'))

    def test_nova_keypairs(self):
        self.exec_verify(['nova', 'keypair-add', 'test key', '--pub-key',
                          cwd('nova_keypair-add.pub')],
                         stdout='')

        self.exec_verify(['nova', 'keypair-list'],
                         filename=cwd('nova_keypair-list'))

        self.exec_verify(['nova', 'keypair-show', 'test key'],
                         filename=cwd('nova_keypair-show'))

        self.exec_verify(['nova', 'keypair-delete', 'test key'],
                         stdout='')

        self.exec_verify(['nova', 'keypair-add', 'test key'],
                         callback=verify_private_key)
