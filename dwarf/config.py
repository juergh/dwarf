#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

from __future__ import print_function

import logging
import os
import yaml

LOG = logging.getLogger(__name__)

_BASE_CONFIG = {
    # Directories
    'instances_dir': '/var/lib/dwarf/instances',
    'instances_base_dir': '/var/lib/dwarf/instances/_base',
    'images_dir': '/var/lib/dwarf/images',

    # Database and logfile
    'dwarf_db': '/var/lib/dwarf/dwarf.db',
    'dwarf_log': '/var/lib/dwarf/dwarf.log',
}

_DEFAULT_CONFIG = {
    'debug': False,

    'libvirt_domain_type': 'kvm',
    'libvirt_bridge_name': 'dwbr0',
    'libvirt_bridge_ip': '10.0.0.1',

    'bind_host': '127.0.0.1',
    'bind_port': 5000,

    'server_soft_reboot_timeout': 30,
    'force_config_drive': True,
}


class _Config(object):

    def __init__(self):
        # Get the config data from file
        cfile = os.path.join(os.path.dirname(__file__), '../etc', 'dwarf.conf')
        if not os.path.exists(cfile):
            cfile = '/etc/dwarf.conf'
        with open(cfile, 'r') as fh:
            opts = yaml.load(fh)

        # Handle empty config files
        if opts is None:
            opts = {}

        # Add base config information
        for (key, val) in _BASE_CONFIG.iteritems():
            opts[key] = val

        # Add default config information
        for (key, val) in _DEFAULT_CONFIG.iteritems():
            if key not in opts:
                opts[key] = val

        # Add the config data as attributes to our object
        for (key, val) in opts.iteritems():
            setattr(self, key, val)

        # Store for later use
        self._options = opts

    def set_option(self, key, val):
        """
        Set a config option
        """
        setattr(self, key, val)
        self._options[key] = val

    def get_options(self):
        """
        Get all config options
        """
        return self._options

    def dump_options(self):
        """
        Dump the options to the logfile
        """
        for key in sorted(self._options.iterkeys()):
            LOG.info('%s: %s', key, self._options[key])


_CONFIG = None


def Config():
    """
    Factory function to return the already created object
    """
    global _CONFIG   # pylint: disable=W0603
    if _CONFIG is None:
        _CONFIG = _Config()
    return _CONFIG
