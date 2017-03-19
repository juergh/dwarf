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

# from tests import data
from tests import utils


def cwd(filename):
    return os.path.join(os.path.dirname(__file__), 'data', filename)


# image1 = data.image['11111111-2222-3333-4444-555555555555']


class DwarfTestCase(utils.TestCase):

    def setUp(self):
        super(DwarfTestCase, self).setUp()
        self.start_dwarf()

    def tearDown(self):
        self.stop_dwarf()
        super(DwarfTestCase, self).tearDown()

    def test_os_catalog(self):
        self.exec_verify(['openstack', 'catalog', 'list'],
                         filename=cwd('os_catalog_list'))

        self.exec_verify(['openstack', 'catalog', 'show', 'Compute'],
                         filename=cwd('os_catalog_show_compute'))

        self.exec_verify(['openstack', 'catalog', 'show', 'Image'],
                         filename=cwd('os_catalog_show_image'))

        self.exec_verify(['openstack', 'catalog', 'show', 'Identity'],
                         filename=cwd('os_catalog_show_identity'))
