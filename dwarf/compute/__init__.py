#!/usr/bin/python

from dwarf.compute import servers
from dwarf.compute import images
from dwarf.compute import keypairs
from dwarf.compute import flavors


class Controller(object):

    def __init__(self):
        self.servers = servers.Controller()
        self.images = images.Controller()
        self.keypairs = keypairs.Controller()
        self.flavors = flavors.Controller()
