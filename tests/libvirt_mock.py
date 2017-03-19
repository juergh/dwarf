#!/usr/bin/env python
#
# Copyright (c) 2017 Hewlett Packard Enterprise Development, L.P.
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
import os
import xmltodict

LOG = logging.getLogger(__name__)

# Original libvirt variables
VIR_DOMAIN_NOSTATE = 0
VIR_DOMAIN_RUNNING = 1
VIR_DOMAIN_BLOCKED = 2
VIR_DOMAIN_PAUSED = 3
VIR_DOMAIN_SHUTDOWN = 4
VIR_DOMAIN_SHUTOFF = 5
VIR_DOMAIN_CRASHED = 6
VIR_DOMAIN_PMSUSPENDED = 7

# Redefined below
_open = open


# Mock variables
IP_ADDRESS = None
DOMAIN_STATE = VIR_DOMAIN_NOSTATE


class LibvirtDomainMock(object):
    """
    Fake libvirt domain class
    """
    def __init__(self, xml):
        self._xml = xmltodict.parse(xml)
        self._basepath = os.path.dirname(self._xml['domain']['devices']['disk']
                                         [0]['source']['@file'])
        self._first_boot = True

    def create(self):
        """
        Create a domain
        """
        LOG.info('libvirt_mock: domain.create()')
        global DOMAIN_STATE   # pylint: disable=W0603

        if self._first_boot:
            self._first_boot = False
            DOMAIN_STATE = VIR_DOMAIN_NOSTATE

            # Create a dummy console log file
            console_log = os.path.join(self._basepath, 'console.log')
            with _open(console_log, 'w') as fh:
                fh.write('Test server console log')

        else:
            DOMAIN_STATE = VIR_DOMAIN_RUNNING

        return self

    def destroy(self):
        """
        Destroy a domain
        """
        LOG.info('libvirt_mock: domain.destroy()')
        global DOMAIN_STATE   # pylint: disable=W0603
        DOMAIN_STATE = VIR_DOMAIN_SHUTDOWN

    def info(self):
        """
        Return domain information
        """
        LOG.info('libvirt_mock: domain.info()')
        return [DOMAIN_STATE, 1024, 1024, 1, 0]

    def shutdown(self):
        """
        Shut down a domain
        """
        LOG.info('libvirt_mock: domain.shutdown()')
        global DOMAIN_STATE   # pylint: disable=W0603
        DOMAIN_STATE = VIR_DOMAIN_SHUTDOWN

    def undefine(self):
        LOG.info('libvirt_mock: domain.undefine()')


class LibvirtNetworkMock(object):
    """
    Fake libvirt network class
    """
    def __init__(self):
        self._first = True

#    def create(self):
#        LOG.info('libvirt_mock: network.create()')
#        pass

    def DHCPLeases(self, mac=''):
        """
        Return DHCP leases
        """
        LOG.info('libvirt_mock: network.DHCPLeases(%s)', mac)
        if IP_ADDRESS is None:
            return []
        return [{'ipaddr': IP_ADDRESS}]

    def isActive(self):
        LOG.info('libvirt_mock: network.isActive()')

    def setAutostart(self, val):
        LOG.info('libvirt_mock: network.setAutoStart(%s)', val)


class LibvirtMock(object):
    """
    Fake libvirt class
    """
    def __init__(self):
        self._domain = None
        self._network = LibvirtNetworkMock()

    def defineXML(self, xml):
        LOG.info('libvirt_mock: libvirt.defineXML(%s...)', xml[0:40])
        # Return a fake domain class
        self._domain = LibvirtDomainMock(xml)
        return self._domain

    def getLibVersion(self):
        LOG.info('libvirt_mock: libvirt.getLibVersion()')
        # Return a fake version number
        return "0123456789"

    def lookupByName(self, name):
        LOG.info('libvirt_mock: libvirt.lookupByName(%s)', name)
        # Return a fake domain class
        return self._domain

#    def networkDefineXML(self, xml):
#        LOG.info('libvirt_mock: libvirt.networkDefineXML()')
        # Return a fake network class
#        return self._network

    def networkLookupByName(self, name):
        LOG.info('libvirt_mock: libvirt.networkLookupByName(%s)', name)
        # Return a fake network class
        return self._network


_LIBVIRT = LibvirtMock()


def open(uri):   # pylint: disable=W0622
    LOG.info('libvirt_mock: open(%s)', uri)
    return _LIBVIRT


class libvirtError(Exception):
    pass
