#!/usr/bin/python

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
