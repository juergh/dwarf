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

import json

from webtest import TestApp

from tests import utils

from dwarf.api_server import ApiServer

VERSION_RESP = {
    'id': 'v2.0',
    'links': [
        {
            'href': 'http://127.0.0.1:20000/compute/v2.0/',
            'rel': 'self',
        },
    ],
    'status': 'CURRENT',
    'updated': '2016-05-11T00:00:00Z',
}


def list_versions_resp():
    return {'versions': [VERSION_RESP]}


def show_version_resp():
    return {'version': VERSION_RESP}


class DwarfTestCase(utils.TestCase):

    def setUp(self):
        super(DwarfTestCase, self).setUp()
        self.app = TestApp(ApiServer().app)

    # Commented out to silence pylint
    # def tearDown(self):
    #     super(DwarfTestCase, self).tearDown()

    def test_list_versions(self):
        resp = self.app.get('/compute', status=300)
        self.assertEqual(json.loads(resp.body), list_versions_resp())

    def test_show_version(self):
        resp = self.app.get('/compute/v2.0', status=200)
        self.assertEqual(json.loads(resp.body), show_version_resp())
