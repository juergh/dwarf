#!/usr/bin/python

import libvirt   # pylint: disable=F0401
import os

from Cheetah.Template import Template

from dwarf.common import utils


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
                'memory': server['flavor']['ram'],
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

    def _get_domain(self, server):
        """
        Get the active server domain
        """
        try:
            domain = self.libvirt.lookupByName(server['domain'])
        except libvirt.libvirtError:
            return
        return domain

    def _destroy_domain(self, domain):
        """
        Destroy a libvirt domain
        """
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
        domain.undefine()

    def boot_server(self, server):
        """
        Boot a server
        """
        self._connect()
        xml = create_libvirt_xml(server)
        self._create_domain(xml)
