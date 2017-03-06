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

from dwarf import db
from dwarf import task
from dwarf import utils

from dwarf.compute import keypairs
from dwarf.image import images

from dwarf.compute.api import ComputeApiServer
from dwarf.identity.api import IdentityApiServer
from dwarf.image.api import ImageApiServer

LOG = logging.getLogger(__name__)

json_render = utils.json_render


class TestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(TestCase, self).__init__(*args, **kwargs)
        self.maxDiff = None
        self.db = None
        self.threads = []
        self.uuid = data.uuid

    def setUp(self):
        """
        Pre-test set up
        """
        super(TestCase, self).setUp()

        # Reset the UUID
        self.uuid = data.uuid

        # Default mocks
        db._now = self.get_now   # pylint: disable=W0212
        uuid.uuid4 = self.get_uuid

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
        return data.now

    def get_uuid(self):
        resp = self.uuid

        # Calcuate the next UUID
        i = int(self.uuid[0:1])
        self.uuid = '%d' % (i + 1) * 8 + '-' + '%d' % (i + 2) * 4 + '-' + \
                    '%d' % (i + 3) * 4 + '-' + '%d' % (i + 4) * 4 + '-' + \
                    '%d' % (i + 5) * 12

        return resp

    # -------------------------------------------------------------------------
    # Database manipulation methods

    def create_image(self, image):
        """
        Create an image in the database
        """
        self.uuid = image['id']
        cp_image = deepcopy(image)
        images.Controller().create(StringIO.StringIO(cp_image['data']),
                                   cp_image)

    def create_keypair(self, keypair):
        """
        Create an SSH keypair in the database
        """
        self.uuid = keypair['id']
        cp_keypair = deepcopy(keypair)
        keypairs.Controller().create(cp_keypair)

    # -------------------------------------------------------------------------
    # Dwarf start/stop methods

    def start_dwarf(self):
        """
        Start all dwarf threads
        """
        self.threads = [
            IdentityApiServer(quiet=True),
            ComputeApiServer(quiet=True),
            ImageApiServer(quiet=True),
        ]
        for t in self.threads:
            t.daemon = True
            t.start()

        alive = True
        active = 0
        while alive and active != len(self.threads):
            time.sleep(1)
            active = 0
            for t in self.threads:
                if not t.is_alive():
                    alive = False
                    break
                if t.is_active():
                    active += 1
        if not alive:
            self.stop_dwarf()
            raise Exception('Dwarf failed to start!')

    def stop_dwarf(self):
        """
        Stop all dwarf threads
        """
        for t in self.threads:
            t.stop()

        # Wait until all threads are stopped
        for t in self.threads:
            t.join()

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

        if error is not None:
            LOG.warn(error)
            LOG.warn('Exit code: %d', p_exitcode)
            LOG.warn('Begin of stdout\n%s\nEnd of stdout', p_stdout)
            LOG.warn('Begin of stderr\n%s\nEnd of stderr', p_stderr)
            LOG.warn('Expected exit code: %d', exitcode)
            LOG.warn('Begin of expected stdout\n%s\nEnd of expected stdout',
                     stdout)
            raise Exception(error)
