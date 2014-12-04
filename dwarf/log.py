#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
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
import sys

from dwarf import config

CONF = config.Config()


class _StreamToLogger(object):
    """
    Helper class to redirect stdout and stderr to the logger
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level

    def write(self, message):
        message = message.rstrip('\n')
        if message != '':
            self.logger.log(self.level, message)


# Set up the logger
_filename = CONF.dwarf_log
_format = '%(asctime)s - %(levelname)s - %(name)s : %(message)s'
_level = logging.DEBUG if CONF.debug else logging.INFO
logging.basicConfig(filename=_filename, format=_format, level=_level)

# Redirect stdout and stderr to the logger
# This needs to run very early before the bottle module is imported
_logger = logging.getLogger(__name__)
sys.stdout = _StreamToLogger(_logger, logging.INFO)
sys.stderr = _StreamToLogger(_logger, logging.ERROR)
