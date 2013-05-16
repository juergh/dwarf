#!/usr/bin/python

from __future__ import print_function

import os

from dwarf import db

from dwarf.compute import flavors
from dwarf.compute import images
from dwarf.compute import virt

from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG

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

        # Create a new server in the database
        _server = self.db.servers.add(name=server['name'], image_id=image_id,
                                      flavor_id=flavor_id,
                                      key_name=server.get('key_name'))
        _server = self._expand(_server)

        server_domain = 'instance-d%07x' % int(_server['id'])

        # Create the base images
        # Need to query the database to get the glance image file location
        _image = self.db.images.show(id=image_id)
        image_file = _image['location'][7:]   # remove 'file://'
        base_images = utils.create_base_images(CONF.instances_base_dir,
                                               image_file, image_id)

        # Create the server base directory and the disk images
        server_base_dir = '%s/%s' % (CONF.instances_dir, server_domain)
        os.makedirs(server_base_dir)
        utils.create_local_images(server_base_dir, base_images)

        return utils.sanitize(_server, SERVERS_INFO)

    def delete(self, server_id):
        """
        Delete a server
        """
        print('compute.servers.delete(server_id=%s)' % server_id)

        self.db.servers.delete(id=server_id)
