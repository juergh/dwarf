#!/usr/bin/python

from __future__ import print_function

from dwarf.compute import servers
from dwarf.compute import images
from dwarf.compute import keypairs


class Controller(object):

    def __init__(self):
        self.servers = servers.Controller()
        self.images = images.Controller()
        self.keypairs = keypairs.Controller()
