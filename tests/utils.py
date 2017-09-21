#!/usr/bin/env python
#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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

import libvirt
import logging
import os
import shutil
import StringIO
import subprocess
import time
import unittest
import uuid

from copy import deepcopy

from tests import data

from dwarf import api_server
from dwarf import db
from dwarf import task
from dwarf import utils

from dwarf.compute import keypairs
from dwarf.compute import servers
from dwarf.image import images

LOG = logging.getLogger(__name__)

json_render = utils.json_render


class TestCase(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None
        self.db = None
        self.dwarf = None

        # Mocking variables
        self.now = data.now
        self.uuid = data.uuid
        self.mac_address = data.mac_address
        self.ip_address = None
        self.domain_state = None

    def setUp(self):
        """
        Pre-test set up
        """
        super(TestCase, self).setUp()

        # Reset the UUID
        self.uuid = data.uuid

        # Default mocks
        uuid.uuid4 = self.get_uuid
        db._now = self.get_now   # pylint: disable=W0212
        servers._generate_mac = self.get_mac_address   # pylint: disable=W0212
        libvirt.get_ip_address = self.get_ip_address
        libvirt.get_domain_state = self.domain_state

        # Create the temp directory tree
        if os.path.exists('/tmp/dwarf'):
            shutil.rmtree('/tmp/dwarf')
        os.makedirs('/tmp/dwarf/images')
        os.makedirs('/tmp/dwarf/instances/_base')

        # Initialize the database
        self.db = db.Controller()
        self.db.init()

    def tearDown(self):
        """
        Post-test tear down
        """
        super(TestCase, self).tearDown()

        # Kill all running tasks (just in case)
        task.stop_all(wait=True)

        # Purge the temp directory tree
        if os.path.exists('/tmp/dwarf'):
            shutil.rmtree('/tmp/dwarf')

    # -------------------------------------------------------------------------
    # Mock methods

    def get_now(self):
        return self.now

    def get_uuid(self):
        return self.uuid

    def get_mac_address(self):
        return self.mac_address

    def get_ip_address(self):
        return self.ip_address

    def get_domain_state(self):
        return self.domain_state

    # -------------------------------------------------------------------------
    # Database manipulation methods

    def create_image(self, image):
        """
        Create an image in the database
        """
        self.uuid = image['id']

        image_dc = deepcopy(image)
        images.Controller().create(image_dc)

        image_fh = StringIO.StringIO(image_dc['data'])
        images.Controller().upload(image_dc['id'], image_fh)

    def create_keypair(self, keypair):
        """
        Create an SSH keypair in the database
        """
        self.uuid = keypair['id']

        keypair_dc = deepcopy(keypair)
        keypairs.Controller().create(keypair_dc)

    # -------------------------------------------------------------------------
    # Dwarf start/stop methods

    def start_dwarf(self):
        """
        Start the API server
        """
        self.dwarf = api_server.ApiServer(quiet=True)
        self.dwarf.start()

        alive = True
        active = False
        while alive and not active:
            time.sleep(1)
            alive = self.dwarf.is_alive()
            active = self.dwarf.is_active()
            if not alive:
                break
        if not alive:
            self.stop_dwarf()
            raise Exception('Dwarf failed to start!')

        print('Dwarf is started')

    def stop_dwarf(self):
        """
        Stop the API server
        """
        self.dwarf.stop()
        self.dwarf.join()

        print('Dwarf is stopped')

    # -------------------------------------------------------------------------
    # Misc helper methods

    def to_headers(self, metadata):
        """
        Convert a dict to an HTTP headers list
        """
        headers = []
        for (key, val) in metadata.iteritems():
            if key == 'properties':
                for (k, v) in val.iteritems():
                    headers.append(('x-image-meta-property-%s' % k, str(v)))
            else:
                headers.append(('x-image-meta-%s' % key, str(val)))
        return headers

    def exec_verify(self, cmd, exitcode=0, filename=None, callback=None,
                    stdout=None):
        """
        Execute an (openstack client) command and verify its exit code and
        stdout
        """
        # Execute the command
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (p_stdout, p_stderr) = p.communicate()
        p.stdin.close()
        p_exitcode = p.returncode

        # Check the response against stored file content
        if filename is not None:
            with open(filename) as fh:
                stdout = fh.read()

        # Check the response using the provided callback function
        elif callback is not None:
            stdout = callback(p_stdout)

        # Check the repsonse against the provided string
        elif stdout is not None:
            pass

        else:
            stdout = ''

        error = None
        if p_exitcode != exitcode:
            error = 'Unexpected exit code!'
        elif p_stdout != stdout:
            error = 'Unexpected stdout response content!'

        print(cmd)
        print(p_stdout)

        if error is not None:
            LOG.error('*******************************************************'
                      '*********')
            LOG.error(error)
            LOG.error('Command: %s', ' '.join(cmd))
            LOG.error('Exit code: %d', p_exitcode)

            LOG.error('BEGIN of stdout\n%s', p_stdout)
            LOG.error('END of stdout')

            LOG.error('BEGIN of stderr\n%s', p_stderr)
            LOG.error('END of stderr\n')

            LOG.error('Expected exit code: %d', exitcode)

            LOG.error('BEGIN of expected stdout\n%s', stdout)
            LOG.error('END of expected stdout')
            LOG.error('*******************************************************'
                      '*********')

            raise Exception(error)
