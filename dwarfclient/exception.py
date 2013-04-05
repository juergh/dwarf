#!/usr/bin/python


class ProcessExecutionError(IOError):

    def __init__(self, cmd=None, exit_code=None, stdout=None, stderr=None,
                 description=None):
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.description = description

        if description is None:
            description = 'Unexpected error while running command'
        if exit_code is None:
            exit_code = '-'
        message = ('%s\ncommand: %s\nexit code: %s\nstdout: %s\nstderr: %s' %
                   (description, cmd, exit_code, stdout, stderr))
        IOError.__init__(self, message)


class DwarfException(Exception):
    """
    Base Dwarf exception
    """
    message = "An unknown exception occurred"

    def __init__(self, message=None, **kwargs):
        if not message:
            message = self.message % kwargs
        super(DwarfException, self).__init__(message)


class ServerBootFailure(DwarfException):
    message = 'Failed to boot server: %(reason)s'


class ServerDeleteFailure(DwarfException):
    message = 'Failed to delete server: %(reason)s'
