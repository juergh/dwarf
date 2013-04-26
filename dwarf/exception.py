#!/usr/bin/python

import sys

from functools import wraps
from bottle import abort


def catchall(func):
    """
    Wrapper to catch all exceptions
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DwarfException as e:
            print('caught DwarfException: %s %s' % (e.code, e.message))
            abort(e.code, e.message)
        except Exception as e:
            (et, ei, tb) = sys.exc_info()
            raise et, ei, tb
    return wrapper

#class ProcessExecutionError(IOError):

#    def __init__(self, cmd=None, exit_code=None, stdout=None, stderr=None,
#                 description=None):
#        self.cmd = cmd
#        self.exit_code = exit_code
#        self.stdout = stdout
#        self.stderr = stderr
#        self.description = description

#        if description is None:
#            description = 'Unexpected error while running command'
#        if exit_code is None:
#            exit_code = '-'
#        message = ('%s\ncommand: %s\nexit code: %s\nstdout: %s\nstderr: %s' %
#                   (description, cmd, exit_code, stdout, stderr))
#        IOError.__init__(self, message)


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


class ServerBootFailure(DwarfException):
    message = 'Failed to boot server: %(reason)s'


class ServerDeleteFailure(DwarfException):
    message = 'Failed to delete server: %(reason)s'


class MetadataStartFailure(DwarfException):
    message = 'Failed to start metadata server" %(reason)s'
