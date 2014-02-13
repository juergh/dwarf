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
#!/usr/bin/python

from __future__ import print_function

import logging
import os
import yaml

LOG = logging.getLogger(__name__)


class _Config(object):

    def __init__(self):
        # Get the config data from file
        cfile = '/etc/dwarf.conf'
        if not os.path.exists(cfile):
            cfile = os.path.join(os.path.dirname(__file__), '../etc',
                                 'dwarf.conf')

        with open(cfile, 'r') as fh:
            cfg = yaml.load(fh)

        # Handle empty config files
        if cfg is None:
            cfg = {}

        # Add base environment information
        cfg['dwarf_dir'] = '/var/lib/dwarf'

        cfg['run_dir'] = os.path.join(cfg['dwarf_dir'], 'run')
        cfg['instances_dir'] = os.path.join(cfg['dwarf_dir'], 'instances')
        cfg['instances_base_dir'] = os.path.join(cfg['instances_dir'], '_base')
        cfg['images_dir'] = os.path.join(cfg['dwarf_dir'], 'images')

        cfg['dwarf_db'] = os.path.join(cfg['dwarf_dir'], 'dwarf.db')
        cfg['dwarf_log'] = os.path.join(cfg['dwarf_dir'], 'dwarf.log')

        # Add the config data as attributes to our object
        for (key, val) in cfg.iteritems():
            setattr(self, key, val)

        # Store for later use
        self._cfg = cfg

    def dump_options(self):
        """
        Dump the options to the logfile
        """
        for key in sorted(self._cfg.iterkeys()):
            LOG.info('%s: %s', key, self._cfg[key])


_CONFIG = None


def Config():
    """
    Factory function to return the already created object
    """
    global _CONFIG   # pylint: disable=W0603
    if _CONFIG is None:
        _CONFIG = _Config()
    return _CONFIG
