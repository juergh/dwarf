#!/usr/bin/python

from __future__ import print_function

from dwarf import db

from dwarf.compute import flavors
from dwarf.compute import images
from dwarf.compute import virt

from dwarf.common import utils

SERVERS_INFO = ('created_at', 'flavor', 'id', 'image', 'links', 'name',
                'status', 'updated_at')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()
        self.flavors = flavors.Controller()
        self.images = images.Controller()
        self.virt = virt.Controller()
#        self.metadata = metadata.Controller(args)

    def _expand(self, server):
        """
        Expand server details
        """
        _image = self.images.show(server['image_id'])
        del server['image_id']
        server['image'] = _image

        _flavor = self.flavors.show(server['flavor_id'])
        del server['flavor_id']
        server['flavor'] = _flavor

        return server

    def list(self):
        """
        List all servers
        """
        print('compute.servers.list()')

        _servers = []
        for s in self.db.servers.list():
            _servers.append(self._expand(s))
        return utils.sanitize(_servers, SERVERS_INFO)

    def show(self, server_id):
        """
        Show server details
        """
        print('compute.servers.show(server_id=%s)' % server_id)

        _server = self.db.servers.show(id=server_id)
        return utils.sanitize(self._expand(_server), SERVERS_INFO)

    def boot(self, server):
        """
        Boot a new server
        """
        print('compute.servers.boot()')

        image_id = server['imageRef']
        flavor_id = server['flavorRef']

        _server = self.db.servers.add(name=server['name'], image_id=image_id,
                                      flavor_id=flavor_id,
                                      key_name=server.get('key_name'))

        return utils.sanitize(self._expand(_server), SERVERS_INFO)

    def delete(self, server_id):
        """
        Delete a server
        """
        print('compute.servers.delete(server_id=%s)' % server_id)

        self.db.servers.delete(id=server_id)
