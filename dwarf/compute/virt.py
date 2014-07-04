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
from dwarf import utils

CONF = config.Config()
LOG = logging.getLogger(__name__)


def _name(sid):
    return 'dwarf-%08x' % int(sid)


def _create_domain_xml(server, force=False):
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
            'memory': int(server['flavor']['ram']) * 1024,
            'vcpus': server['flavor']['vcpus'],
            'basepath': basepath,
            'mac_addr': server['mac_address'],
            'bridge': CONF.libvirt_bridge_name,
        }
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
        'dhcp_start': '.'.join(CONF.libvirt_bridge_ip.split('.')[0:3]+['2']),
        'dhcp_end': '.'.join(CONF.libvirt_bridge_ip.split('.')[0:3]+['255']),
    }

    return Template(xml_template).substitute(xml_info)


class Controller(object):

    def __init__(self):
        self.libvirt = None

    def _connect(self):
        """
        Open a connection to the libvirt daemon
        """
        if self.libvirt is None:
            self.libvirt = libvirt.open('qemu:///system')

    def _create_domain(self, xml, flags=0):
        """
        Create the libvirt domain and start it
        """
        domain = self.libvirt.defineXML(xml)
        domain.createWithFlags(flags)
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
            retval = e.get_error_code()
            if retval == libvirt.VIR_ERR_OPERATION_INVALID:
                # If the instance is already shut off, we get this:
                # Code=5 Error=Requested operation is not valid:
                # domain is not running
                (state, dummy_max_mem, dummy_mem, dummy_vcpus, dummy_time) = \
                    domain.info()
                if state == 5:
                    return
            raise

    def _undefine_domain(self, domain):
        """
        Undefine a libvirt domain
        """
        if domain is None:
            return

        domain.undefine()

    def boot_server(self, server):
        """
        Boot a server
        """
        LOG.info('boot_server(server=%s)', server)

        self._connect()
        xml = _create_domain_xml(server)
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

    def create_network(self):
        """
        Create the network
        """
        LOG.info('create_network()')

        self._connect()
        try:
            # Check if the network exists already
            net = self.libvirt.networkLookupByName('dwarf')
            return
        except libvirt.libvirtError:
            pass

        # Define and create (start) the network
        xml = _create_net_xml()
        net = self.libvirt.networkDefineXML(xml)
        net.create()
        net.setAutostart(1)

        # Add the iptables route for the Ec2 metadata service
        utils.execute(['iptables',
                       '-t', 'nat',
                       '-A', 'PREROUTING',
                       '-s', '%s/24' % CONF.libvirt_bridge_ip,
                       '-d', '169.254.169.254/32',
                       '-p', 'tcp',
                       '-m', 'tcp',
                       '--dport', 80,
                       '-j', 'REDIRECT',
                       '--to-port', CONF.ec2_metadata_port],
                      run_as_root=True,
                      check_exit_code=False)

    def delete_network(self):
        """
        Delete the network
        """
        LOG.info('delete_network()')

        self._connect()
        try:
            # Check if the network exists already
            net = self.libvirt.networkLookupByName('dwarf')
        except libvirt.libvirtError:
            return

        # Destroy (stop) and undefine the network
        net.destroy()
        net.undefine()

        # Delete the iptables route for the Ec2 metadata service
        utils.execute(['iptables',
                       '-t', 'nat',
                       '-D', 'PREROUTING',
                       '-s', '%s/24' % CONF.libvirt_bridge_ip,
                       '-d', '169.254.169.254/32',
                       '-p', 'tcp',
                       '-m', 'tcp',
                       '--dport', 80,
                       '-j', 'REDIRECT',
                       '--to-port', CONF.ec2_metadata_port],
                      run_as_root=True,
                      check_exit_code=False)


VIRT = Controller()
