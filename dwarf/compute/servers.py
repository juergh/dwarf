#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import random
import os
import shutil
import time

from dwarf import config
from dwarf import task
from dwarf import utils

from dwarf.compute import virt
from dwarf.db import DB

from dwarf.compute.flavors import FLAVORS
from dwarf.compute.images import IMAGES
from dwarf.compute.keypairs import KEYPAIRS
from dwarf.compute.virt import VIRT

CONF = config.Config()
LOG = logging.getLogger(__name__)

SERVERS_INFO = ('id', 'links', 'name')
SERVERS_DETAIL = ('created_at', 'flavor', 'id', 'image', 'key_name', 'links',
                  'name', 'status', 'updated_at', 'addresses')

SERVER_BUILDING = 'building'
SERVER_ACTIVE = 'active'
SERVER_STOPPED = 'stopped'
SERVER_PAUSED = 'paused'
SERVER_SUSPENDED = 'suspended'
SERVER_ERROR = 'error'

_VIRT_SERVER_STATE = {
    virt.DOMAIN_NOSTATE: SERVER_BUILDING,
    virt.DOMAIN_RUNNING: SERVER_ACTIVE,
    virt.DOMAIN_PAUSED: SERVER_PAUSED,
    virt.DOMAIN_SHUTDOWN: SERVER_STOPPED,
    virt.DOMAIN_CRASHED: SERVER_ERROR,
    virt.DOMAIN_SUSPENDED: SERVER_SUSPENDED,
}


def _generate_mac():
    """
    Generate a random MAC address
    """
    mac = [0x52, 0x54, 0x00,
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(['%02x' % x for x in mac])


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

    def _update_ip(self, server):
        """
        Update the DHCP assigned IP address
        """
        # Get the DHCP lease information
        lease = VIRT.get_dhcp_lease(server)
        if lease is None:
            return

        # Update the database
        server = DB.servers.update(id=server['id'], ip=lease['ip'])
        return lease['ip']

    def _extend(self, server):
        """
        Extend the server details
        """
        if 'image_id' in server:
            server['image'] = IMAGES.show(server['image_id'])
            del server['image_id']

        if 'flavor_id' in server:
            server['flavor'] = FLAVORS.show(server['flavor_id'])
            del server['flavor_id']

        if 'ip' in server:
            server['addresses'] = {'private': [{'addr': server['ip'],
                                                'version': 4}]}
            del server['ip']

        return server

    def _update_status(self, server):
        """
        Update the (volatile) status of the server
        """
        info = VIRT.info_server(server)
        server['status'] = _VIRT_SERVER_STATE[info['state']]
        return server

    # -------------------------------------------------------------------------
    # Server operations (public)

    def setup(self):
        """
        Setup on start
        """
        LOG.info('setup()')

        VIRT.create_network()

    def teardown(self):
        """
        Teardown on exit
        """
        LOG.info('teardown()')

        VIRT.delete_network()

    def list(self, detail=True):
        """
        List all servers
        """
        LOG.info('list(detail=%s)', detail)

        servers = []
        for s in DB.servers.list():
            servers.append(self._extend(self._update_status(s)))
        if detail:
            return utils.sanitize(servers, SERVERS_DETAIL)
        else:
            return utils.sanitize(servers, SERVERS_INFO)

    def show(self, server_id):
        """
        Show server details
        """
        LOG.info('show(server_id=%s)', server_id)

        server = DB.servers.show(id=server_id)
        return utils.sanitize(self._extend(self._update_status(server)),
                              SERVERS_DETAIL)

    def boot(self, server):
        """
        Boot a new server
        """
        LOG.info('boot(server=%s)', server)

        name = server['name']
        image_id = server['imageRef']
        flavor_id = server['flavorRef']
        key_name = server.get('key_name', None)

        # Sanity checks, will throw exceptions if they fail
        IMAGES.exists(image_id)
        FLAVORS.exists(flavor_id)
        if key_name is not None:
            KEYPAIRS.exists(key_name)

        # Create a new server in the database
        server = DB.servers.create(name=name, image_id=image_id,
                                   flavor_id=flavor_id, key_name=key_name,
                                   status=SERVER_BUILDING)
        server_id = server['id']

        # Generate some more server properties and update the database
        mac_address = _generate_mac()
        server = DB.servers.update(id=server_id, mac_address=mac_address)

        # Extend the server details
        server = self._extend(server)

        # Create the server directory
        basepath = os.path.join(CONF.instances_dir, server_id)
        os.makedirs(basepath)

        # Create the server disk images
        _create_disks(server)

        # Finally boot the server
        VIRT.boot_server(server)

        # Start a task to wait for the server to get its DHCP IP address
        task.start(server_id, 2, 60/2, self._update_ip, server)

        return utils.sanitize(self._extend(self._update_status(server)),
                              SERVERS_DETAIL)

    def delete(self, server_id):
        """
        Delete a server
        """
        LOG.info('delete(server_id=%s)', server_id)

        server = DB.servers.show(id=server_id)

        # Stop all running tasks associated with this server
        task.stop(server_id)

        # Kill the running server
        VIRT.delete_server(server)

        # Purge all server files
        basepath = os.path.join(CONF.instances_dir, server_id)
        if os.path.exists(basepath):
            shutil.rmtree(basepath)

        # Delete the database entry
        DB.servers.delete(id=server['id'])

    def console_log(self, server_id):
        """
        Return the server console log
        """
        LOG.info('console_log(server_id=%s)', server_id)

        console_log = os.path.join(CONF.instances_dir, server_id,
                                   'console.log')

        # Make the console log readable
        utils.execute(['chown', os.getuid(), console_log], run_as_root=True)

        with open(console_log) as fh:
            data = fh.read()
        return unicode(data, errors='ignore')

    def reboot(self, server_id, hard=False):
        """
        Reboot a server
        """
        LOG.info('reboot(server_id=%s, hard=%s)', server_id, hard)

        self.stop(server_id, hard=hard)

        # Check the status of the server
        server = DB.servers.show(id=server_id)
        for dummy in range(0, CONF.server_soft_reboot_timeout/2):
            server = self._update_status(server)
            if server['status'] != SERVER_ACTIVE:
                break
            time.sleep(2)

        # Shut the server down hard if it ignored the soft request
        if hard is False and server['status'] == SERVER_ACTIVE:
            self.stop(server_id, hard=True)
            time.sleep(2)

        self.start(server_id)

    def start(self, server_id):
        """
        Start a server
        """
        LOG.info('start(server_id=%s)', server_id)

        server = DB.servers.show(id=server_id)
        VIRT.start_server(server)

    def stop(self, server_id, hard=False):
        """
        Stop a server
        """
        LOG.info('stop(server_id=%s, hard=%s)', server_id, hard)

        server = DB.servers.show(id=server_id)
        VIRT.stop_server(server, hard)


SERVERS = Controller()
