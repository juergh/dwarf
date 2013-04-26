#!/usr/bin/python

from __future__ import print_function

import os
import yaml


class Config(object):

    def __init__(self):
        # Get the config data from file
        cfile = '/etc/dwarf/dwarf.cfg'
        if not os.path.exists(cfile):
            cfile = os.path.join(os.path.dirname(__file__), '../../etc',
                                 'dwarf.cfg')

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


CONFIG = Config()
