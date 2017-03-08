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

    def test_glance(self):
        # Preload a test image
        self.create_image(image1)

        self.exec_verify(['glance', 'image-list'],
                         filename=cwd('glance_image-list'))

        self.exec_verify(['glance', '--verbose', 'image-list'],
                         filename=cwd('glance_verbose-image-list'))

        self.exec_verify(['glance', 'image-show',
                          '11111111-2222-3333-4444-555555555555'],
                         filename=cwd('glance_image-show'))

        self.exec_verify(['glance', 'image-delete',
                          '11111111-2222-3333-4444-555555555555'],
                         stdout='')

        image1_file = '/tmp/dwarf/test_image_1'
        with open(image1_file, 'w') as fh:
            fh.write(image1['data'])

        self.exec_verify(['glance', 'image-create',
                          '--name', image1['name'],
                          '--container-format', image1['container_format'],
                          '--disk-format', image1['disk_format'],
                          '--file', image1_file],
                         filename=cwd('glance_image-create'))
