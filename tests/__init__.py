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

import sys
import uuid

from mock import MagicMock

from tests import libvirt_mock
from tests import utils

from dwarf import config
from dwarf import db


# Set the test environment
CONF = config.Config()
CONF.set_option('instances_dir', '/tmp/dwarf/instances')
CONF.set_option('instances_base_dir', '/tmp/dwarf/instances/_base')
CONF.set_option('images_dir', '/tmp/dwarf/images')
CONF.set_option('dwarf_db', '/tmp/dwarf/dwarf.db')
CONF.set_option('dwarf_log', '/tmp/dwarf/dwarf.log')

# Mock libvirt imports
# This means that all libvirt calls will be handled by our libvirt_mock module
sys.modules['libvirt'] = libvirt_mock

# Default mocks
db._now = MagicMock(return_value=utils.now)   # pylint: disable=W0212
uuid.uuid4 = MagicMock(return_value=utils.uuid)
