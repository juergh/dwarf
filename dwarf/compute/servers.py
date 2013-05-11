#!/usr/bin/python

from __future__ import print_function

from dwarf import db


class Controller(object):

    def __init__(self):
        self.db = db.Controller()
#        self.virt = virt.Controller(args)
#        self.metadata = metadata.Controller(args)

    def list(self):
        """
        List all servers
        """
        print('compute.servers.list()')
        return self.db.servers.list()
