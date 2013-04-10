#!/usr/bin/python

import libvirt   # pylint: disable=F0401
import os

from Cheetah.Template import Template
from xml.dom import minidom

from dwarfclient.common import config
from dwarfclient.common import utils


CONF = config.CONF

_LIBVIRT_DOMAIN_STATE = {
    0: "NOSTATE",
    1: "RUNNING",
    2: "BLOCKED",
    3: "PAUSED",
    4: "SHUTDOWN",
    5: "SHUTOFF",
    6: "CRASHED",
    7: "SUSPENDED",
}


def _create_libvirt_xml(server, force=False):
    """
    Create a libvirt XML file for the server
    """
    xml_file = '%s/libvirt.xml' % server.basepath

    # Check if the XML file exists already and return its content
    if not force and os.path.exists(xml_file):
        with open(xml_file, 'r') as fh:
            xml = fh.read()
        return xml

    xml_template = open(os.path.join(os.path.dirname(__file__),
                                     'libvirt.xml.template')).read()

    xml_info = {'name': server.domain,
                'memory': server.memory,
                'vcpus': server.vcpus,
                'basepath': server.basepath,
                'mac_addr': utils.generate_mac(),
                'bridge': 'virbr0',
                'host': utils.get_local_ip()}

    xml = str(Template(xml_template, searchList=[xml_info]))

    with open(xml_file, 'w') as fh:
        fh.write(xml)

    return xml


class Controller(object):

    def __init__(self, args):
        self.args = args
        self.libvirt = None

    def _connect(self):
        """
        Open a connection to libvirtd
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
        try:
            domain = self.libvirt.lookupByName(server.domain)
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
                if _LIBVIRT_DOMAIN_STATE[state] == 'SHUTOFF':
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
        xml = _create_libvirt_xml(server)
        self._create_domain(xml)

    def delete_server(self, server):
        """
        Delete a server
        """
        self._connect()
        domain = self._get_domain(server)
        if not domain:
            return
        self._destroy_domain(domain)
        self._undefine_domain(domain)

    def update_server(self, server):
        """
        Update the server object with information from libvirt
        """
        self._connect()
        domain = self._get_domain(server)
        if not domain:
            return

        try:
            xml = domain.XMLDesc(0)
        except libvirt.libvirtError:
            return
        dom = minidom.parseString(xml)

        # Get VNC information
        tag = dom.getElementsByTagName('graphics')[0]
        if tag.getAttribute('type') == 'vnc':
            host = str(tag.getAttribute('listen'))
            port = int(tag.getAttribute('port')) - 5900
            server.add_details({'vnc_display': '%s:%d' % (host, port)})

        # Get network information
        tag = dom.getElementsByTagName('interface')[0]
        if tag.getAttribute('type') == 'bridge':
            mac = tag.getElementsByTagName('mac')[0].\
                getAttribute('address')
            bridge = tag.getElementsByTagName('source')[0].\
                getAttribute('bridge')
            server.add_details({'mac_address': mac, 'bridge': bridge})

        # Get the VM's IP
        server.add_details({'ip_address': utils.find_ip(mac)})

    def reboot_server(self, server):
        """
        Reboot a server
        """
        self.delete_server(server)
        self.boot_server(server)
