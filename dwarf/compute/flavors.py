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
from dwarf import utils

LOG = logging.getLogger(__name__)

FLAVORS_INFO = ('id', 'links', 'name')
FLAVORS_DETAIL = ('disk', 'id', 'links', 'name', 'ram', 'vcpus')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self, detail=True):
        """
        List all flavors
        """
        LOG.info('list(detail=%s)', detail)

        flavors = self.db.flavors.list()
        if detail:
            return utils.sanitize(flavors, FLAVORS_DETAIL)
        else:
            return utils.sanitize(flavors, FLAVORS_INFO)

    def show(self, flavor_id):
        """
        Show flavor details
        """
        LOG.info('show(flavor_id=%s)', flavor_id)

        flavor = self.db.flavors.show(id=flavor_id)
        return utils.sanitize(flavor, FLAVORS_DETAIL)

    def create(self, flavor):
        """
        Create a flavor
        """
        LOG.info('create(flavor=%s)', flavor)

        new_flavor = self.db.flavors.create(**flavor)
        return utils.sanitize(new_flavor, FLAVORS_DETAIL)

    def delete(self, flavor_id):
        """
        Delete a flavor
        """
        LOG.info('delete(flavor_id=%s)', flavor_id)

        self.db.flavors.delete(id=flavor_id)

    def exists(self, flavor_id):
        """
        Check if a flavor exists
        """
        LOG.info('exists(flavor_id=%s)', flavor_id)
        self.db.flavors.show(id=flavor_id)
