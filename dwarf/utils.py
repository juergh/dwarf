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

import json
import logging
import os
import signal
import subprocess

from bottle import SimpleTemplate

from dwarf import exception

LOG = logging.getLogger(__name__)


def show_request(req):
    LOG.debug('---- BEGIN REQUEST HEADERS -----')
    for key in req.headers.keys():
        LOG.debug('%s = %s', key, req.headers[key])
    LOG.debug('---- END REQUEST HEADERS -----')


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
        raise exception.CommandExecutionError(reason='%s\nexit_code: %s\n'
                                              'stdout: %s\nstderr: %s' %
                                              (cmd, exit_code, stdout, stderr))

    if stdout:
        LOG.info('execute(stdout=%s)', stdout)
    if stderr:
        LOG.info('execute(stderr=%s)', stderr)
    return (stdout, stderr)


def template_single(templ, data, add_if_present=None, add=None):
    resp = {}
    for key in templ:
        resp[key] = data[key]

    if add_if_present is not None and add_if_present in data:
        resp[add_if_present] = data[add_if_present]

    if add is not None:
        resp.update(add)

    return resp


def template(templ, data, **kwargs):
    if isinstance(data, (list, tuple)):
        resp = []
        for d in data:
            resp.append(template_single(templ, d, **kwargs))
    else:
        resp = template_single(templ, data, **kwargs)
    return resp


def json_render(template, *args, **kwargs):
    """
    Simple JSON rendering function that renders a JSON-style template and
    returns a (JSON) dict.
    template: JSON-style rendering template.
    *args:    Postitional arguments are dicts containing sets of rendering
              variables and values.
    **kwargs: Keyword arguments are single rendering variables and values.
    """
    # Create a single dict containing all the provided rendering data
    render_data = {}
    for arg in args:
        render_data.update(arg)
    render_data.update(kwargs)

    # Encode string values to take care of multi-line strings. Otherwise the
    # rendered result contains illegal JSON data.
    for key, val in render_data.iteritems():
        if isinstance(val, str):
            render_data[key] = val.encode('string_escape')

    # Do the actual template rendering and convert to a dict
    tpl = SimpleTemplate(template, noescape=True)
    try:
        return json.loads(tpl.render(render_data))
    except:
        LOG.error('Bad JSON syntax:\n%s', tpl.render(render_data))
        raise
