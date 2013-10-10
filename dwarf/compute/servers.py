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
from dwarf.compute import keypairs
from dwarf.compute import virt

CONF = config.CONFIG
LOG = logging.getLogger(__name__)

SERVERS_INFO = ('created_at', 'flavor', 'id', 'image', 'key_name', 'links',
                'name', 'status', 'updated_at', 'addresses')


def _create_disks(server):
    """
    Create the base (backing) and server disk images
    """
    server_id = server['id']
    image_id = server['image']['id']
    image_file = server['image']['location'][7:]   # remove 'file://'
    disk_size = server['flavor']['disk']
    disk_local_size = server['flavor'].get('ephemeral', 10)

    # Create the base boot disk at:
    # instances/_base/<image_id>_<disk_size>
    base_disk = os.path.join(CONF.instances_base_dir,
                             '%s_%s' % (image_id, disk_size))
    if not os.path.exists(base_disk):
        try:
            utils.execute(['qemu-img', 'convert', '-O', 'raw', image_file,
                           base_disk])
            utils.execute(['qemu-img', 'resize', base_disk, '%sG' % disk_size])
        except:
            if os.path.exists(base_disk):
                os.remove(base_disk)
            raise

    # Create the base ephemeral disk at:
    # instances/_base/ephemeral_<disk_local_size>
    base_disk_local = os.path.join(CONF.instances_base_dir,
                                   'ephemeral_%s' % disk_local_size)
    if not os.path.exists(base_disk_local):
        try:
            utils.execute(['qemu-img', 'create', '-f', 'raw', base_disk_local,
                           '%sG' % disk_local_size])
            utils.execute(['mkfs.ext3', '-F', '-L', 'ephemeral0',
                           base_disk_local])
        except:
            if os.path.exists(base_disk_local):
                os.remove(base_disk_local)
            raise

    # Create the server disk at:
    # instances/<server_id>/disk
    server_disk = os.path.join(CONF.instances_dir, server_id, 'disk')
    utils.execute(['qemu-img', 'create', '-f', 'qcow2', '-o',
                   'cluster_size=2M,backing_file=%s' % base_disk, server_disk])

    # Create the server ephemeral disk at:
    # instances/<server_id>/disk_local
    server_disk_local = os.path.join(CONF.instances_dir, server_id,
                                     'disk.local')
    utils.execute(['qemu-img', 'create', '-f', 'qcow2', '-o',
                   'cluster_size=2M,backing_file=%s' % base_disk_local,
                   server_disk_local])


class Controller(object):

    def __init__(self):
        self.db = db.Controller()
        self.flavors = flavors.Controller()
        self.images = images.Controller()
        self.virt = virt.Controller()
        self.keypairs = keypairs.Controller()

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
        # Try to get the server's DHCP-assigned IP
        ip = utils.get_server_ip(server['mac_address'])
        if ip is None:
            return False

        # Update the database and metadata server
        server = self.db.servers.update(id=server['id'], ip=ip,
                                        status='ACTIVE')

        # Add the iptables route for the Ec2 metadata service
        utils.add_ec2metadata_route(server['ip'], CONF.ec2_metadata_port)

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
                                     flavor_id=flavor_id, key_name=key_name,
                                     status='BUILDING')
        server_id = server['id']

        # Generate some more server properties and update the database
        mac_address = utils.generate_mac()
        server = self.db.servers.update(id=server_id, mac_address=mac_address)

        # Extend the server details
        server = self._extend(server)

        # Create the server directory and disk images
        os.makedirs(os.path.join(CONF.instances_dir, server_id))
        _create_disks(server)

        # Finally boot the server
        self.virt.boot_server(server)

        # Update the status of the server
        server = self.db.servers.update(id=server_id, status='NETWORKING')

        # Schedule a timer to wait for the server to get its DHCP IP address
        utils.timer_start(server_id, 2, 60/2, [True],
                          self._wait_for_ip, server)

        return utils.sanitize(server, SERVERS_INFO)

    def delete(self, server_id):
        """
        Delete a server
        """
        LOG.info('delete(server_id=%s)', server_id)

        server = self.db.servers.show(id=server_id)

        # Delete the iptables route for the Ec2 metadata service
        utils.delete_ec2metadata_route(server['ip'], CONF.ec2_metadata_port)

        # Kill the running instance
        self.virt.delete_server(server)

        # Purge all instance files
        basepath = os.path.join(CONF.instances_dir, server_id)
        if os.path.exists(basepath):
            shutil.rmtree(basepath)

        # Delete the database entry
        self.db.servers.delete(id=server['id'])

    def console_log(self, server_id):
        """
        Return the server console log
        """
        console_log = os.path.join(CONF.instances_dir, server_id,
                                   'console.log')

        # Make the console log readable
        utils.execute(['chown', os.getuid(), console_log], run_as_root=True)

        with open(console_log) as fh:
            data = fh.read()
        return data

    def reboot(self, server_id, hard=False):
        """
        Reboot a server
        """
        LOG.info('reboot(server_id=%s, hard=%s)', server_id, hard)

        server = self.db.servers.show(id=server_id)

        utils.delete_ec2metadata_route(server['ip'], CONF.ec2_metadata_port)
        self.virt.delete_server(server)
        self.virt.boot_server(server)
        utils.add_ec2metadata_route(server['ip'], CONF.ec2_metadata_port)
