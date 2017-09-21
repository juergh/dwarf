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

import json
import logging
import random
import os
import shutil
import time

from dwarf import config
from dwarf import db
from dwarf import task
from dwarf import utils

from dwarf.compute import flavors
from dwarf.compute import keypairs
from dwarf.compute import virt

from dwarf.image import images

CONF = config.Config()
LOG = logging.getLogger(__name__)

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


def _create_disks(server, image, flavor):
    """
    Create the base (backing) and server disk images
    """
    server_id = server['id']
    image_id = image['id']
    image_file = image['file']
    disk_size = flavor['disk']
    disk_local_size = flavor.get('ephemeral', 10)

    # Create the base boot disk at:
    # instances/_base/<image_id>_<disk_size>
    base_disk = os.path.join(CONF.instances_base_dir,
                             '%s_%s' % (image_id, disk_size))
    if not os.path.exists(base_disk):
        try:
            utils.execute(['qemu-img', 'convert', '-O', 'raw', image_file,
                           base_disk])
            utils.execute(['qemu-img', 'resize', base_disk, '%sG' % disk_size])
        except Exception:   # pylint: disable=W0703
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
        except Exception:   # pylint: disable=W0703
            if os.path.exists(base_disk_local):
                os.remove(base_disk_local)
            raise

    # Create the server disk at:
    # instances/<server_id>/disk
    server_disk = os.path.join(CONF.instances_dir, server_id, 'disk')
    utils.execute(['qemu-img', 'create', '-f', 'qcow2', '-o',
                   'cluster_size=2M,backing_file=%s' % base_disk, server_disk])

    # Create the server ephemeral disk at:
    # instances/<server_id>/disk.local
    server_disk_local = os.path.join(CONF.instances_dir, server_id,
                                     'disk.local')
    utils.execute(['qemu-img', 'create', '-f', 'qcow2', '-o',
                   'cluster_size=2M,backing_file=%s' % base_disk_local,
                   server_disk_local])


def _create_config_drive(server, keypair):
    """
    Create the config drive for the server
    """
    if not (CONF.force_config_drive or server['config_drive'] == 'True'):
        return

    # Config drive data
    config_data = {
        'vendor_data': {
        },
        'meta_data': {
            'availability_zone': 'dwarf',
            'hostname': '%s.dwarflocal' % server['name'],
            'launch_index': 0,
            'name': server['name'],
            'uuid': server['id'],
        },
    }

    # Add the SSH keypair info
    if keypair is not None:
        config_data['meta_data']['public_keys'] = {
            keypair['name']: keypair['public_key']
        }

    # Create a temporary directory containing the config drive data
    config_dir = os.path.join('/tmp', 'dwarf-config-drive-%s' % server['id'])
    if os.path.exists(config_dir):
        shutil.rmtree(config_dir)

    for version in ['latest', '2013-10-17']:
        data_dir = os.path.join(config_dir, 'openstack', version)
        os.makedirs(data_dir)
        for data in ['vendor_data', 'meta_data']:
            data_file = os.path.join(data_dir, '%s.json' % data)
            with open(data_file, 'w') as fh:
                json.dump(config_data[data], fh)

    # Create the server config drive at:
    # instances/<server_id>/disk.config
    server_disk_config = os.path.join(CONF.instances_dir, server['id'],
                                      'disk.config')
    utils.execute(['genisoimage', '-o', server_disk_config, '-ldots',
                   '-allow-lowercase', '-allow-multidot', '-l', '-quiet', '-J',
                   '-r', '-V', 'config-2', config_dir])

    # Remove the temporary directory
    shutil.rmtree(config_dir)


class Controller(object):

    def __init__(self):
        self.db = db.Controller()
        self.flavors = flavors.Controller()
        self.images = images.Controller()
        self.keypairs = keypairs.Controller()
        self.virt = virt.Controller()

    def _update_ip(self, server):
        """
        Update the DHCP assigned IP address
        """
        # Get the DHCP lease information
        lease = self.virt.get_dhcp_lease(server)
        if lease is None:
            return

        # Update the database
        server = self.db.servers.update(id=server['id'], ip=lease['ip'])
        return lease['ip']

    def _update_status(self, server):
        """
        Update the (volatile) status of the server
        """
        info = self.virt.info_server(server)
        if info and 'state' in info:
            server['status'] = _VIRT_SERVER_STATE[info['state']]
        return server

    # -------------------------------------------------------------------------
    # Server operations (public)

    def setup(self):
        """
        Setup on start
        """
        LOG.info('setup()')

        self.virt.create_network()

    def teardown(self):
        """
        Teardown on exit
        """
        LOG.info('teardown()')

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

    def create(self, server):
        """
        Create a new server
        """
        LOG.info('create(server=%s)', server)

        name = server['name']
        image_id = server['imageRef']
        flavor_id = server['flavorRef']
        key_name = server.get('key_name', None)
        config_drive = server.get('config_drive', False)

        # Get the associated image, flavor and keypair
        image = self.images.show(image_id)
        flavor = self.flavors.show(flavor_id)
        if key_name is None:
            keypair = None
        else:
            keypair = self.keypairs.show(key_name)

        # Create a new server in the database
        server = self.db.servers.create(name=name, image_id=image_id,
                                        flavor_id=flavor_id, key_name=key_name,
                                        config_drive=config_drive,
                                        status=SERVER_BUILDING)
        server_id = server['id']

        # Generate some more server properties and update the database
        mac_address = _generate_mac()
        server = self.db.servers.update(id=server_id, mac_address=mac_address)

        # Create the server directory
        basepath = os.path.join(CONF.instances_dir, server_id)
        os.makedirs(basepath)

        # Create the server disk images and config drive
        _create_disks(server, image, flavor)
        _create_config_drive(server, keypair)

        # Finally create the server
        self.virt.create_server(server, flavor)

        # Start a task to wait for the server to get its DHCP IP address
        task.start(server_id, 2, 60 / 2, self._update_ip, server)

        return self._update_status(server)

    def delete(self, server_id):
        """
        Delete a server
        """
        LOG.info('delete(server_id=%s)', server_id)

        server = self.db.servers.show(id=server_id)

        # Stop all running tasks associated with this server
        task.stop(server_id)

        # Kill the running server
        self.virt.delete_server(server)

        # Purge all server files
        basepath = os.path.join(CONF.instances_dir, server_id)
        if os.path.exists(basepath):
            shutil.rmtree(basepath)

        # Delete the database entry
        self.db.servers.delete(id=server['id'])

    def list(self):
        """
        List all servers
        """
        LOG.info('list()')

        servers = []
        for s in self.db.servers.list():
            servers.append(self._update_status(s))

        return servers

    def reboot(self, server_id, hard=False):
        """
        Reboot a server
        """
        LOG.info('reboot(server_id=%s, hard=%s)', server_id, hard)

        self.stop(server_id, hard=hard)

        # Check the status of the server
        server = self.db.servers.show(id=server_id)
        for dummy in range(0, CONF.server_soft_reboot_timeout / 2):
            server = self._update_status(server)
            if server['status'] != SERVER_ACTIVE:
                break
            time.sleep(2)

        # Shut the server down hard if it ignored the soft request
        if hard is False and server['status'] == SERVER_ACTIVE:
            self.stop(server_id, hard=True)
            time.sleep(2)

        self.start(server_id)

    def show(self, server_id):
        """
        Show server details
        """
        LOG.info('show(server_id=%s)', server_id)

        server = self.db.servers.show(id=server_id)
        return self._update_status(server)

    def start(self, server_id):
        """
        Start a server
        """
        LOG.info('start(server_id=%s)', server_id)

        server = self.db.servers.show(id=server_id)
        self.virt.start_server(server)

    def stop(self, server_id, hard=False):
        """
        Stop a server
        """
        LOG.info('stop(server_id=%s, hard=%s)', server_id, hard)

        server = self.db.servers.show(id=server_id)
        self.virt.stop_server(server, hard)
