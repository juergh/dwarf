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

from tests import utils
from webtest import TestApp

from dwarf.compute.api import ComputeApiServer

SHOW_VERSION_RESP = {
    'version': {
        'id': 'v1.1',
        'links': [
            {
                'href': 'http://127.0.0.1:8774/v1.1/',
                'rel': 'self',
            },
        ],
        'status': 'CURRENT',
        'updated': '2016-05-11T00:00:00Z',
    },
}

LIST_VERSIONS_RESP = {
    'versions': [SHOW_VERSION_RESP['version']]
}


class ApiTestCase(utils.TestCase):

    def setUp(self):
        super(ApiTestCase, self).setUp()
        self.app = TestApp(ComputeApiServer().app)

    def tearDown(self):
        super(ApiTestCase, self).tearDown()

    def test_http_error(self):
        self.app.get('/no-such-url', status=404)

    def test_list_versions(self):
        resp = self.app.get('/', status=300)
        self.assertEqual(json.loads(resp.body), LIST_VERSIONS_RESP)

    def test_show_version(self):
        resp = self.app.get('/v1.1', status=200)
        self.assertEqual(json.loads(resp.body), SHOW_VERSION_RESP)
