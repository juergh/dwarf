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

import libvirt
import logging
import os
import uuid

from string import Template

from dwarf import config

CONF = config.Config()
LOG = logging.getLogger(__name__)

DOMAIN_NOSTATE = 0
DOMAIN_RUNNING = 1
DOMAIN_PAUSED = 2
DOMAIN_SHUTDOWN = 3
DOMAIN_CRASHED = 4
DOMAIN_SUSPENDED = 5

_LIBVIRT_DOMAIN_STATE = {
    libvirt.VIR_DOMAIN_NOSTATE: DOMAIN_NOSTATE,
    libvirt.VIR_DOMAIN_RUNNING: DOMAIN_RUNNING,
    libvirt.VIR_DOMAIN_BLOCKED: DOMAIN_RUNNING,
    libvirt.VIR_DOMAIN_PAUSED: DOMAIN_PAUSED,
    libvirt.VIR_DOMAIN_SHUTDOWN: DOMAIN_SHUTDOWN,
    libvirt.VIR_DOMAIN_SHUTOFF: DOMAIN_SHUTDOWN,
    libvirt.VIR_DOMAIN_CRASHED: DOMAIN_CRASHED,
    libvirt.VIR_DOMAIN_PMSUSPENDED: DOMAIN_SUSPENDED,
}


def _name(sid):
    return 'dwarf-%08x' % int(sid)


def _xml_snippet(name, enable):
    xml = {}
    if enable:
        xml['%s_begin' % name] = ''
        xml['%s_end' % name] = ''
    else:
        xml['%s_begin' % name] = '<!--'
        xml['%s_end' % name] = '-->'
    return xml


def _create_domain_xml(server, flavor, force=False):
    """
    Create a libvirt XML file for the domain
    """
    basepath = os.path.join(CONF.instances_dir, server['id'])
    xml_file = os.path.join(basepath, 'libvirt.xml')

    # Read the XML file if it exists already
    if not force and os.path.exists(xml_file):
        LOG.info('read existing libvirt.xml for server %s', server['id'])

        with open(xml_file, 'r') as fh:
            xml = fh.read()

    # Otherwise create it
    else:
        LOG.info('create libvirt.xml for server %s', server['id'])

        with open(os.path.join(os.path.dirname(__file__),
                               'libvirt-domain.xml'), 'r') as fh:
            xml_template = fh.read()

        xml_info = {
            'domain_type': CONF.libvirt_domain_type,
            'uuid': server['id'],
            'name': _name(server['int_id']),
            'memory': int(flavor['ram']) * 1024,
            'vcpus': flavor['vcpus'],
            'basepath': basepath,
            'mac_addr': server['mac_address'],
            'bridge': CONF.libvirt_bridge_name,
        }

        # Enable/disable the config drive
        config_drive = _xml_snippet('config_drive',
                                    (CONF.force_config_drive or
                                     server['config_drive'] == 'True'))
        xml_info.update(config_drive)

        xml = Template(xml_template).substitute(xml_info)
        with open(xml_file, 'w') as fh:
            fh.write(xml)

    return xml


def _create_net_xml():
    """
    Create a libvirt XML for the network bridge
    """
    with open(os.path.join(os.path.dirname(__file__),
                           'libvirt-net.xml'), 'r') as fh:
        xml_template = fh.read()

    xml_info = {
        'uuid': str(uuid.uuid4()),
        'bridge': CONF.libvirt_bridge_name,
        'ip': CONF.libvirt_bridge_ip,
        'dhcp_start': '.'.join(CONF.libvirt_bridge_ip.split('.')[0:3] + ['2']),
        'dhcp_end': '.'.join(CONF.libvirt_bridge_ip.split('.')[0:3] + ['254']),
    }

    return Template(xml_template).substitute(xml_info)


class Controller(object):

    def __init__(self):
        self.libvirt = None

    def _test_connect(self):
        """
        Test the connection to the libvirt daemon
        """
        try:
            self.libvirt.getLibVersion()
            return True
        except libvirt.libvirtError as e:
            if e.get_error_code() in (libvirt.VIR_ERR_SYSTEM_ERROR,
                                      libvirt.VIR_ERR_INTERNAL_ERROR):
                LOG.debug('Connection to libvirt broke')
                return False
            raise

    def _connect(self):
        """
        Open a connection to the libvirt daemon
        """
        if self.libvirt is None or not self._test_connect():
            uri = 'qemu:///system'
            LOG.debug('Connecting to libvirt (%s)', uri)
            self.libvirt = libvirt.open(uri)

    # -------------------------------------------------------------------------
    # Libvirt domain operations (private)

    def _create_domain(self, xml):
        """
        Create the libvirt domain and start it
        """
        domain = self.libvirt.defineXML(xml)
        domain.create()
        return domain

    def _get_domain(self, server):
        """
        Get the active server domain
        """
        try:
            domain = self.libvirt.lookupByName(_name(server['int_id']))
        except libvirt.libvirtError:
            return
        return domain

    def _destroy_domain(self, domain):
        """
        Destroy a libvirt domain
        """
        if domain is None:
            return

        try:
            domain.destroy()
        except libvirt.libvirtError as e:
            if e.get_error_code() == libvirt.VIR_ERR_OPERATION_INVALID:
                # Check if the instance is already shut down
                if self._info_domain(domain)['state'] == DOMAIN_SHUTDOWN:
                    return
            raise

    def _undefine_domain(self, domain):
        """
        Undefine a libvirt domain
        """
        if domain is None:
            return
        domain.undefine()

    def _start_domain(self, domain):
        """
        Start a libvirt domain
        """
        if domain is None:
            return
        if self._info_domain(domain)['state'] == DOMAIN_RUNNING:
            return

        domain.create()

    def _info_domain(self, domain):
        """
        Return the libvirt domain info
        """
        if domain is None:
            return

        info = dict(zip(['state', 'max_mem', 'memory', 'nr_virt_cpu',
                         'cpu_time'], domain.info()))
        # Normalize the domain state
        info['state'] = _LIBVIRT_DOMAIN_STATE[info['state']]
        return info

    def _shutdown_domain(self, domain, hard):
        """
        Shutdown a libvirt domain
        """
        if domain is None:
            return
        if self._info_domain(domain)['state'] != DOMAIN_RUNNING:
            return

        if hard:
            self._destroy_domain(domain)
        else:
            domain.shutdown()

    # -------------------------------------------------------------------------
    # Server operations (public)

    def create_server(self, server, flavor):
        """
        Create a server
        """
        LOG.info('create_server(server=%s, flavor=%s)', server, flavor)

        self._connect()
        xml = _create_domain_xml(server, flavor)
        self._create_domain(xml)

    def delete_server(self, server):
        """
        Delete a server
        """
        LOG.info('delete_server(server=%s)', server)

        self._connect()
        domain = self._get_domain(server)
        self._destroy_domain(domain)
        self._undefine_domain(domain)

    def start_server(self, server):
        """
        Start a server
        """
        LOG.info('start_server(server=%s)', server)

        self._connect()
        domain = self._get_domain(server)
        self._start_domain(domain)

    def stop_server(self, server, hard=False):
        """
        Stop a server
        """
        LOG.info('stop_server(server=%s, hard=%s)', server, hard)

        self._connect()
        domain = self._get_domain(server)
        self._shutdown_domain(domain, hard)

    def info_server(self, server):
        """
        Return the server info
        """
        LOG.info('info_server(server=%s)', server)

        self._connect()
        domain = self._get_domain(server)
        info = self._info_domain(domain)
        LOG.info('info = %s', info)
        return info

    def create_network(self):
        """
        Create the network
        """
        LOG.info('create_network()')

        self._connect()
        try:
            # Check if the network already exists
            net = self.libvirt.networkLookupByName('dwarf')
        except libvirt.libvirtError as e:
            if e.get_error_code() != libvirt.VIR_ERR_NO_NETWORK:
                # Unexpected error
                raise
            # Define the network
            xml = _create_net_xml()
            net = self.libvirt.networkDefineXML(xml)

        # Configure the network to automatically start on host boot
        net.setAutostart(1)

        # Create (start) the network
        if net.isActive() == 0:
            net.create()

    def get_dhcp_lease(self, server):
        """
        Get DHCP lease information
        """
        LOG.info('get_dhcp_lease(server=%s)', server)

        net = self.libvirt.networkLookupByName('dwarf')
        lease = net.DHCPLeases(mac=server['mac_address'])
        if len(lease) == 1:
            return {'ip': lease[0]['ipaddr']}
