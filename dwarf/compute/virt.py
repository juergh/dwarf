#!/usr/bin/python

import libvirt   # pylint: disable=F0401
import logging
import os

from Cheetah.Template import Template

from dwarf.common import utils

LOG = logging.getLogger(__name__)


def create_libvirt_xml(server, force=False):
    """
    Create a libvirt XML file for the server
    """
    xml_file = '%s/libvirt.xml' % server['basepath']

    # Check if the XML file exists already and return its content
    if not force and os.path.exists(xml_file):
        with open(xml_file, 'r') as fh:
            xml = fh.read()
        return xml

    xml_template = open(os.path.join(os.path.dirname(__file__),
                                     'libvirt.xml.template')).read()

    xml_info = {'name': server['domain'],
                'memory': int(server['flavor']['ram']) * 1024,
                'vcpus': server['flavor']['vcpus'],
                'basepath': server['basepath'],
                'mac_addr': utils.generate_mac(),
                'bridge': 'virbr0',
                'host': utils.get_local_ip()}

    xml = str(Template(xml_template, searchList=[xml_info]))

    with open(xml_file, 'w') as fh:
        fh.write(xml)

    return xml


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

    def _get_domain(self, domain_name):
        """
        Get the active server domain
        """
        try:
            domain = self.libvirt.lookupByName(domain_name)
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
                (state, _max_mem, _mem, _vcpus, _time) = domain.info()
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
        xml = create_libvirt_xml(server)
        self._create_domain(xml)

        return server

    def delete_server(self, server_id):
        """
        Delete a server
        """
        LOG.info('delete_server(server_id=%s)', server_id)

        self._connect()
        domain = self._get_domain(utils.id2domain(server_id))
        self._destroy_domain(domain)
        self._undefine_domain(domain)
