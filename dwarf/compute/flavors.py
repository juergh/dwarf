#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

from __future__ import print_function

import logging

from dwarf import db

LOG = logging.getLogger(__name__)


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def create(self, flavor):
        """
        Create a flavor
        """
        LOG.info('create(flavor=%s)', flavor)
        return self.db.flavors.create(**flavor)

    def delete(self, flavor_id):
        """
        Delete a flavor
        """
        LOG.info('delete(flavor_id=%s)', flavor_id)
        return self.db.flavors.delete(id=flavor_id)

    def list(self):
        """
        List all flavors
        """
        LOG.info('list()')
        return self.db.flavors.list()

    def show(self, flavor_id):
        """
        Show flavor details
        """
        LOG.info('show(flavor_id=%s)', flavor_id)
        return self.db.flavors.show(id=flavor_id)
