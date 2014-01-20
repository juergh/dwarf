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
import os
import random
import signal
import subprocess
import time

from threading import Thread

from dwarf import exception

LOG = logging.getLogger(__name__)

_TIMER = {}


class _Timer(Thread):

    def __init__(self, tid, interval, repeat, exit_on_retval,
                 func, *args, **kwargs):
        super(_Timer, self).__init__()

        self.tid = tid
        self.interval = interval
        self.repeat = repeat
        self.exit_on_retval = exit_on_retval
        self.check_retval = isinstance(exit_on_retval, list)

        self.func = func
        self.args = args
        self.kwargs = kwargs

        self._stop = False

    def run(self):
        for dummy in range(self.repeat):
            time.sleep(self.interval)
            if self._stop:
                break
            retval = self.func(*self.args, **self.kwargs)
            if self.check_retval and retval in self.exit_on_retval:
                break

    def stop(self):
        self._stop = True


def sanitize(obj, keys):

    def _sanitize(obj, keys):
        fields = {}
        for k in keys:
            if k in obj:
                fields[k] = obj[k]
            elif k == 'links':
                fields[k] = []
            elif k == 'properties':
                fields[k] = {}
            else:
                fields[k] = None
        return fields

    if isinstance(obj, dict):
        return _sanitize(obj, keys)

    objs = []
    for o in obj:
        objs.append(_sanitize(o, keys))
    return objs


def show_request(req):
    LOG.debug('---- BEGIN REQUEST HEADERS -----')
    for key in req.headers.keys():
        LOG.debug('%s = %s', key, req.headers[key])
    LOG.debug('---- END REQUEST HEADERS -----')


def generate_mac():
    """
    Generate a random MAC address
    """
    mac = [0x52, 0x54, 0x00,
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(['%02x' % x for x in mac])


def get_server_ip(mac):
    """
    Get the IP associated with the given MAC address
    """
    addr = None
    leases = '/var/lib/libvirt/dnsmasq/default.leases'
    with open(leases, 'r') as fh:
        for line in fh.readlines():
            col = line.split()
            if col[1] == mac:
                addr = col[2]
                break

    LOG.info('get_server_ip(mac=%s) : %s', mac, addr)
    return addr


def execute(cmd, check_exit_code=None, shell=False, run_as_root=False):
    """
    Helper function to execute a command
    """
    LOG.info('execute(cmd=%s, check_exit_code=%s, shell=%s, run_as_root=%s)',
             cmd, check_exit_code, shell, run_as_root)

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
        raise exception.CommandExecutionFailure(code=exit_code,
                                                reason='cmd: %s, stdout: %s, '
                                                'stderr: %s' % (cmd, stdout,
                                                                stderr))

    if stdout:
        LOG.info('execute(stdout=%s)', stdout)
    if stderr:
        LOG.info('execute(stderr=%s)', stderr)
    return (stdout, stderr)


def timer_start(tid, interval, repeat, exit_on_retval,
                func, *args, **kwargs):
    """
    Start a new timer
    """
    LOG.info('timer_start(tid=%s, interval=%s, repeat=%s, exit_on_retval=%s, '
             'func=%s, args=%s, kwargs=%s)', tid, interval, repeat,
             exit_on_retval, func.__name__, args, kwargs)

    t = _Timer(tid, interval, repeat, exit_on_retval, func, *args, **kwargs)
    _TIMER[tid] = t
    t.start()


def timer_stop(tid):
    """
    Stop a running timer
    """
    LOG.info('timer_stop(tid=%s)', tid)

    t = _TIMER[tid]
    del _TIMER[tid]
    t.stop()


def add_ec2metadata_route(ip, port):
    """
    Add the iptables route for the Ec2 metadata service
    """
    LOG.info('add_ec2metadata_route(ip=%s, port=%s)', ip, port)

    # Add the route
    execute(['iptables',
             '-t', 'nat',
             '-A', 'PREROUTING',
             '-s', ip,
             '-d', '169.254.169.254/32',
             '-p', 'tcp',
             '-m', 'tcp',
             '--dport', 80,
             '-j', 'REDIRECT',
             '--to-port', port],
            run_as_root=True)


def delete_ec2metadata_route(ip, port):
    """
    Delete a (compute) server from the metadata server
    """
    LOG.info('delete_ec2metadata_route(ip=%s, port=%s)', ip, port)

    # Delete the route
    execute(['iptables',
             '-t', 'nat',
             '-D', 'PREROUTING',
             '-s', ip,
             '-d', '169.254.169.254/32',
             '-p', 'tcp',
             '-m', 'tcp',
             '--dport', 80,
             '-j', 'REDIRECT',
             '--to-port', port],
            run_as_root=True,
            check_exit_code=False)
