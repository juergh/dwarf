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

from functools import wraps
from bottle import response, abort

LOG = logging.getLogger(__name__)


def catchall(func):
    """
    Wrapper to catch all exceptions
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DwarfException as e:
            LOG.warn('caught DwarfException: %s (%s)', e.code, e.message)
            response.content_type = 'application/json; charset=UTF-8'
            abort(e.code, e.message)
        except Exception as e:
            LOG.exception('caught unknown exception')
    return wrapper


class DwarfException(Exception):
    """
    Base Dwarf exception
    """
    message = "An unknown exception occurred"
    code = 500

    def __init__(self, **kwargs):
        if 'code' in kwargs:
            self.code = kwargs['code']
        self.message = self.message % kwargs
        super(DwarfException, self).__init__(self.message)


class Failure(DwarfException):
    message = '%(reason)s'


class Forbidden(DwarfException):
    message = '%(reason)s'
    code = 403


class NotFound(DwarfException):
    message = '%(reason)s'
    code = 404


class Conflict(DwarfException):
    message = '%(reason)s'
    code = 409


class ServerBootFailure(DwarfException):
    message = 'Failed to boot server: %(reason)s'


class ServerDeleteFailure(DwarfException):
    message = 'Failed to delete server: %(reason)s'


class MetadataStartFailure(DwarfException):
    message = 'Failed to start metadata server" %(reason)s'


class CommandExecutionFailure(DwarfException):
    message = 'Failed to run command" %(reason)s'
