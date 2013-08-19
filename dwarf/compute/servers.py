#!/usr/bin/python

from __future__ import print_function

import logging
import os
import shutil

from dwarf import db

from dwarf.common import config
from dwarf.common import utils

from dwarf.compute import ec2metadata
from dwarf.compute import flavors
from dwarf.compute import images
from dwarf.compute import virt

CONF = config.CONFIG
LOG = logging.getLogger(__name__)

SERVERS_INFO = ('created_at', 'flavor', 'id', 'image', 'key_name', 'links',
                'name', 'status', 'updated_at', 'addresses')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()
        self.flavors = flavors.Controller()
        self.images = images.Controller()
        self.virt = virt.Controller()
        self.ec2metadata = ec2metadata.Controller()

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

        if 'ip' in server:
            server['addresses'] = {'private': [{'addr': server['ip'],
                                                'version': 4}]}
            del server['ip']

        return server

#    def _reduce(self, server):
#        """
#        Reduce server details
#        """
#        if 'image' in server:
#            server['image_id'] = server['image']['id']
#            del server['image']
#
#        if 'flavor' in server:
#            server['flavor_id'] = server['flavor']['id']
#            del server['flavor']
#
#        if 'addresses' in server:
#            server['ip'] = server['addresses']['private'][0]['addr']
#            del server['addresses']
#
#        return server

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

    def _wait_for_ip(self, server):
        """
        Update the DHCP assigned IP address
        """
        ip = utils.get_ip(server['mac_address'])
        if ip is None:
            return False

        # Update the database and metadata server
        server = self.db.servers.update(id=server['id'], ip=ip,
                                        status='ACTIVE')
        self.ec2metadata.add_server(server)

        return True

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

        # Generate some more server properties and update the database
        domain = utils.id2domain(server['id'])
        mac_address = utils.generate_mac()
        server = self.db.servers.update(id=server['id'], domain=domain,
                                        mac_address=mac_address)

        # Extend the server details
        server = self._extend(server)

        # Create the base images
        image_file = server['image']['location'][7:]   # remove 'file://'
        base_images = utils.create_base_images(CONF.instances_base_dir,
                                               image_file, image_id)

        # Create the server base directory and the disk images
        basepath = os.path.join(CONF.instances_dir, domain)
        os.makedirs(basepath)
        utils.create_local_images(basepath, base_images)

        # Finally boot the server
        self.virt.boot_server(server)

        # Schedule a timer to wait for the server to get its DHCP IP address
        utils.timer_start(domain, 2, 60/2, [True], self._wait_for_ip, server)

        return utils.sanitize(server, SERVERS_INFO)

    def delete(self, server_id):
        """
        Delete a server
        """
        LOG.info('delete(server_id=%s)', server_id)

        server = self.db.servers.show(id=server_id)

        # Nuke the metadata server
        self.ec2metadata.delete_server(server)

        # Kill the running instance
        self.virt.delete_server(server)

        # Purge all instance files
        basepath = os.path.join(CONF.instances_dir, server['domain'])
        if os.path.exists(basepath):
            shutil.rmtree(basepath)

        # Delete the database entry
        self.db.servers.delete(id=server['id'])

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
