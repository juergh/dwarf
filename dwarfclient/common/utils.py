#!/usr/bin/python

from __future__ import print_function

import hashlib
import os
import prettytable
import random
import signal
import socket
import subprocess

from dwarfclient.common import log

from dwarfclient import exception

LOG = log.LOG


def _dec(name, *args, **kwargs):
    """
    Decorator for subcommand arguments and help text
    """
    def _decorator(func):
        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault(name, []).insert(0, (args, kwargs))
        return func
    return _decorator


def add_help(*args, **kwargs):
    return _dec('help', *args, **kwargs)


def add_arg(*args, **kwargs):
    return _dec('arg', *args, **kwargs)


def print_list(objs, fields, sort=True, reverse=True):
    """
    Pretty print a list of objects or dicts
    """
    pt = prettytable.PrettyTable([f for f in fields], caching=False)
    for f in fields:
        try:
            # prettytable < 0.6
            pt.set_field_align(f, 'l')
        except AttributeError:
            # prettytable >= 0.6
            pt.align['f'] = 'l'

    for obj in objs:
        row = []
        for field in fields:
            fname = field.lower().replace(' ', '_')
            if isinstance(obj, dict):
                data = obj.get(fname, None)
            else:
                data = getattr(obj, fname, None)
            row.append(data)
        pt.add_row(row)

    if sort:
        print(pt.get_string(sortby=fields[0], reversesort=reverse))
    else:
        print(pt.get_string())


def print_details(obj, fields=None):
    """
    Print object details
    """
    if obj is None:
        return

    details = []

    # Get all variables from the object
    if fields is None:
        for key in obj.__dict__.keys():
            details.append({'property': key, 'value': obj.__dict__[key]})

    # Get only select variables from the object
    else:
        for field in fields:
            fname = field.lower().replace(' ', '_')
            if fname in obj.__dict__:
                data = obj.__dict__[fname]
            else:
                data = 'N/A'
            details.append({'property': field, 'value': data})

    print_list(details, ['Property', 'Value'], sort=False)


def create_base_images(target_dir, image):
    """
    Create the boot and ephemeral disk base images if they don't exist
    """
    LOG.debug("utils.create_base_images: target_dir='%s', image='%s'",
              target_dir, image)

    # Boot disk base image
    md5sum = hashlib.md5(open(image).read()).hexdigest()
    boot_disk = '%s/%s' % (target_dir, md5sum)
    if not os.path.exists(boot_disk):
        try:
            execute(['qemu-img', 'convert', '-O', 'raw', image, boot_disk])
        except:
            if os.path.exists(boot_disk):
                os.remove(boot_disk)
            raise

    # Ephemeral disk base image
    ephemeral_disk = '%s/ephemeral_0_10_None' % target_dir
    if not os.path.exists(ephemeral_disk):
        try:
            execute(['qemu-img', 'create', '-f', 'raw', ephemeral_disk, '10G'])
            execute(['mkfs.ext3', '-F', '-L', 'ephemeral0', ephemeral_disk])
        except:
            if os.path.exists(ephemeral_disk):
                os.remove(ephemeral_disk)
            raise

    return {'boot-disk': boot_disk, 'ephemeral-disk': ephemeral_disk}


def create_local_images(target_dir, base_images):
    """
    Create the boot and ephemeral disk images
    """
    LOG.debug("utils.create_local_images: target_dir='%s', base_images='%s'",
              target_dir, base_images)

    # Boot disk (disk)
    disk = '%s/disk' % target_dir
    execute(['qemu-img', 'create', '-f', 'qcow2', '-o',
             'cluster_size=2M,backing_file=%s' % base_images['boot-disk'],
             disk])

    # Ephemeral disk (disk.local)
    # TODO: variable size
    disk_local = '%s/disk.local' % target_dir
    execute(['qemu-img', 'create', '-f', 'qcow2', '-o',
             'cluster_size=2M,backing_file=%s' % base_images['ephemeral-disk'],
             disk_local])

    return {'disk': disk, 'disk.local': disk_local}


def execute(cmd, check_exit_code=None, shell=False, run_as_root=False):
    """
    Helper function to execute a command
    """
    LOG.debug("utils.execute: cmd=%s, check_exit_code=%s, shell=%s", cmd,
              check_exit_code, shell)

    def preexec_fn():
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    if check_exit_code is None:
        check_exit_code = [0]

    ignore_exit_code = False
    if isinstance(check_exit_code, bool):
        ignore_exit_code = not check_exit_code
        check_exit_code = [0]
    elif isinstance(check_exit_code, int):
        check_exit_code = [check_exit_code]

    if run_as_root and os.geteuid() != 0:
        cmd = ['sudo'] + cmd

    cmd = [str(i) for i in cmd]

    if shell:
        cmd = ' '.join(cmd)

    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, close_fds=True, shell=shell,
                         preexec_fn=preexec_fn)
    (stdout, stderr) = p.communicate()
    p.stdin.close()
    exit_code = p.returncode

    if not ignore_exit_code and exit_code not in check_exit_code:
        raise exception.ProcessExecutionError(cmd=' '.join(cmd),
                                              exit_code=exit_code,
                                              stdout=stdout,
                                              stderr=stderr)

    if stdout:
        LOG.debug('utils.execute: stdout: %s', stdout)
    if stderr:
        LOG.debug('utils.execute: stderr: %s', stderr)
    return (stdout, stderr)


def get_local_ip():
    """
    Return the IP of the local machine
    """
    addr = '127.0.0.1'
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, _port) = csock.getsockname()
        csock.close()
    except socket.error:
        pass

    LOG.debug("utils.get_local_ip: addr=%s", addr)
    return addr


def find_ip(mac):
    """
    Find the IP associated with the given MAC address
    """
    addr = None
    for line in execute(['arp', '-n'])[0].splitlines():
        col = line.split()
        if col[2] == mac:
            addr = col[0]
            break

    LOG.debug("utils.find_ip: mac=%s, addr=%s", mac, addr)
    return addr


def generate_mac():
    mac = [0x52, 0x54, 0x00,
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(['%02x' % x for x in mac])
