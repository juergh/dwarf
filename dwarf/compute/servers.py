#!/usr/bin/python

from __future__ import print_function

import logging
import os
import shutil

from dwarf import db

from dwarf.common import config
from dwarf.common import utils
from dwarf.compute import flavors
from dwarf.compute import images
from dwarf.compute import virt

CONF = config.CONFIG
LOG = logging.getLogger(__name__)

SERVERS_INFO = ('created_at', 'flavor', 'id', 'image', 'key_name', 'links',
                'name', 'status', 'updated_at')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()
        self.flavors = flavors.Controller()
        self.images = images.Controller()
        self.virt = virt.Controller()
#        self.metadata = metadata.Controller(args)

    def _extend(self, server):
        """
        Extend server details
        """
        if 'image_id' in server:
            server['image'] = self.images.show(server['image_id'])
            del server['image_id']

        if 'flavor_id' in server:
            server['flavor'] = self.flavors.show(server['flavor_id'])
            del server['flavor_id']

        return server

    def _reduce(self, server):
        """
        Reduce server details
        """
        if 'image' in server:
            server['image_id'] = server['image']['id']
            del server['image']

        if 'flavor' in server:
            server['flavor_id'] = server['flavor']['id']
            del server['flavor']

        return server

    def list(self):
        """
        List all servers
        """
        LOG.info('list()')

        servers = []
        for s in self.db.servers.list():
            servers.append(self._extend(s))
        return utils.sanitize(servers, SERVERS_INFO)

    def show(self, server_id):
        """
        Show server details
        """
        LOG.info('show(server_id=%s)', server_id)

        server = self.db.servers.show(id=server_id)
        return utils.sanitize(self._extend(server), SERVERS_INFO)

    def boot(self, server):
        """
        Boot a new server
        """
        LOG.info('boot(server=%s)', server)

        name = server['name']
        image_id = server['imageRef']
        flavor_id = server['flavorRef']
        key_name = server.get('key_name')

        # Add a new server to the database
        server = self.db.servers.add(name=name, image_id=image_id,
                                     flavor_id=flavor_id, key_name=key_name)
        server = self._extend(server)

        server['domain'] = utils.id2domain(server['id'])
        server['basepath'] = '%s/%s' % (CONF.instances_dir, server['domain'])

        # Create the base images
        # Need to query the database to get the glance image file location
        image = self.db.images.show(id=image_id)
        image_file = image['location'][7:]   # remove 'file://'
        base_images = utils.create_base_images(CONF.instances_base_dir,
                                               image_file, image_id)

        # Create the server base directory and the disk images
        os.makedirs(server['basepath'])
        utils.create_local_images(server['basepath'], base_images)

        # Boot the server
        server = self.virt.boot_server(server)

        # Update the database
        server = self.db.servers.update(**self._reduce(server))

        return utils.sanitize(server, SERVERS_INFO)

    def delete(self, server_id):
        """
        Delete a server
        """
        LOG.info('delete(server_id=%s)', server_id)

        # Kill the running instance
        self.virt.delete_server(server_id)

        # Purge all instance files
        basepath = '%s/%s' % (CONF.instances_dir, utils.id2domain(server_id))
        if os.path.exists(basepath):
            shutil.rmtree(basepath)

        # Delete the database entry
        self.db.servers.delete(id=server_id)

    def console_log(self, server_id):
        """
        Return the server console log
        """
        console_log = os.path.join(CONF.instances_dir,
                                   utils.id2domain(server_id), 'console.log')

        # Make the console log readable
        utils.execute(['chown', os.getuid(), console_log], run_as_root=True)

        with open(console_log) as fh:
            data = fh.read()
        return data
