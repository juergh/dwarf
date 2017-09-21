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

import libvirt
import os
import time

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


server1 = data.server['11111111-2222-3333-4444-555555555555']
server1_image = data.image[server1['image_id']]


class DwarfTestCase(utils.TestCase):

    def setUp(self):
        super(DwarfTestCase, self).setUp()
        self.start_dwarf()

    def tearDown(self):
        self.stop_dwarf()
        super(DwarfTestCase, self).tearDown()

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

    def test_nova_servers(self):
        # Preload an image
        self.create_image(server1_image)

        self.exec_verify(['nova', 'boot', '--flavor', server1['flavor_id'],
                          '--image', server1['image_id'], server1['name']],
                         filename=cwd('nova_boot'))

        self.exec_verify(['nova', 'list'],
                         filename=cwd('nova_list.building'))

        libvirt.DOMAIN_STATE = libvirt.VIR_DOMAIN_RUNNING
        libvirt.IP_ADDRESS = server1['ip']
        time.sleep(3)

        # Should show the IP and status 'active'
        self.exec_verify(['nova', 'list'],
                         filename=cwd('nova_list'))

        self.exec_verify(['nova', 'show', server1['id']],
                         filename=cwd('nova_show'))

        self.exec_verify(['nova', 'console-log', server1['id']],
                         stdout='Test server console log\n')

        self.exec_verify(['nova', 'stop', server1['id']],
                         stdout='Request to stop server %s has been '
                         'accepted.\n' % server1['id'])

        # Should show status 'stopped'
        self.exec_verify(['nova', 'show', server1['id']],
                         filename=cwd('nova_show.stopped'))

        self.exec_verify(['nova', 'start', server1['id']],
                         stdout='Request to start server %s has been '
                         'accepted.\n' % server1['id'])

        # Should show status 'active'
        self.exec_verify(['nova', 'show', server1['id']],
                         filename=cwd('nova_show'))

        self.exec_verify(['nova', 'reboot', server1['id']],
                         stdout='Request to reboot server <Server: %s> has '
                         'been accepted.\n' % server1['name'])
