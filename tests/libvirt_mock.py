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

LOG = logging.getLogger(__name__)

VIR_DOMAIN_NOSTATE = 0
VIR_DOMAIN_RUNNING = 1
VIR_DOMAIN_BLOCKED = 2
VIR_DOMAIN_PAUSED = 3
VIR_DOMAIN_SHUTDOWN = 4
VIR_DOMAIN_SHUTOFF = 5
VIR_DOMAIN_CRASHED = 6
VIR_DOMAIN_PMSUSPENDED = 7


class LibvirtDomainMock(object):
    """
    Fake libvirt domain class
    """
    def __init__(self):
        self._info = [VIR_DOMAIN_NOSTATE, 1024, 1024, 1, 0]

    def create(self):
        LOG.info('libvirt_mock: domain.create()')
        return self

#    def destroy(self):
#        LOG.info('libvirt_mock: domain.destroy()')
#        pass

    def info(self):
        LOG.info('libvirt_mock: domain.info()')
        return self._info

#    def shutdown(self):
#        LOG.info('libvirt_mock: domain.shutdown()')
#        pass

#    def undefine(self):
#        LOG.info('libvirt_mock: domain.undefine()')
#        pass


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
        LOG.info('libvirt_mock: network.DHCPLeases(%s)', mac)
        if self._first:
            self._first = False
            return []
        return [{'ipaddr': '10.10.10.5'}]

    def isActive(self):
        LOG.info('libvirt_mock: network.isActive()')

    def setAutostart(self, val):
        LOG.info('libvirt_mock: network.setAutoStart(%s)', val)


class LibvirtMock(object):
    """
    Fake libvirt class
    """
    def __init__(self):
        self._domain = LibvirtDomainMock()
        self._network = LibvirtNetworkMock()

    def defineXML(self, xml):
        LOG.info('libvirt_mock: libvirt.defineXML(%s...)', xml[0:40])
        # Return a fake domain class
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
