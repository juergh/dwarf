#!/usr/bin/python

from __future__ import print_function

import os
import shutil

from dwarfclient import db
from dwarfclient import servers

from dwarfclient.common import config
from dwarfclient.common import log

CONF = config.CONF
LOG = log.LOG


class Client(object):

    def __init__(self, args):
        self.args = args
        self.servers = servers.Controller(args)
        self.db = db.Controller(args)

    def init(self):
        """
        Initialize the Dwarf environment
        """
        LOG.debug('client.init')

        # Create the directory structure
        print('Creating directory tree %s' % CONF.dwarf_dir)
        for d in ['instances_dir', 'instances_base_dir']:
            os.makedirs(getattr(CONF, d))

        # Initialize the database
        print('Initializing the database')
        self.db.init()

    def purge(self):
        """
        Purge the Dwarf environment
        """
        LOG.debug('client.purge')

        if os.path.exists(CONF.dwarf_dir):
            print('Are you sure you want to delete %s/* [y/N]: ' %
                  CONF.dwarf_dir, end='')
            choice = raw_input().lower()
            if choice in ['y', 'yes']:
                for f in os.listdir(CONF.dwarf_dir):
                    f = '%s/%s' % (CONF.dwarf_dir, f)
                    try:
                        os.remove(f)
                    except OSError:
                        shutil.rmtree(f)
