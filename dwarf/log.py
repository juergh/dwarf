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


def init_logger(redirect_stdio=True, log_to_stdout=False, log_level=None):
    """
    Initialize/configure the logger
    """
    if log_level is None:
        log_level = logging.DEBUG if CONF.debug else logging.INFO

    log_format = '%(asctime)s - %(levelname)s - %(name)s : %(message)s'

    if log_to_stdout:
        logging.basicConfig(stream=sys.stdout, format=log_format,
                            level=log_level)
    else:
        logging.basicConfig(filename=CONF.dwarf_log, format=log_format,
                            level=log_level)

    if redirect_stdio:
        # Redirect stdout and stderr to the logger
        logger = logging.getLogger(__name__)
        sys.stdout = _StreamToLogger(logger, logging.INFO)
        sys.stderr = _StreamToLogger(logger, logging.ERROR)

        # Hack to redirect bottle's stdout and stderr
        import bottle
        bottle._stdout = sys.stdout.write   # pylint: disable=W0212
        bottle._stderr = sys.stderr.write   # pylint: disable=W0212
