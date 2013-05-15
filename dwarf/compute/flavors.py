#!/usr/bin/python

from __future__ import print_function

from dwarf import db

from dwarf.common import utils

FLAVORS_INFO = ('disk', 'id', 'links', 'name', 'ram', 'vcpus')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self):
        """
        List all flavors
        """
        print('compute.flavors.list()')
        _flavors = self.db.flavors.list()
        return utils.sanitize(_flavors, FLAVORS_INFO)

    def show(self, flavor_id):
        """
        Show flavor details
        """
        print('compute.flavors.show(flavor_id=%s)' % flavor_id)
        _flavor = self.db.flavors.show(id=flavor_id)
        return utils.sanitize(_flavor, FLAVORS_INFO)
