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
import time

from threading import Thread

LOG = logging.getLogger(__name__)

_TASK = {}


def _add_task(tid, task):
    LOG.info('_add_task(tid=%s, task=%s)', tid, task)
    _TASK[tid] = task


def _get_task(tid):
    LOG.info('_get_task(tid=%s)', tid)
    return _TASK.get(tid, None)


def _pop_task(tid):
    LOG.info('_pop_task(tid=%s)', tid)
    return _TASK.pop(tid, None)


class _Task(Thread):

    def __init__(self, tid, interval, repeat, exit_on_retval, func, *args,
                 **kwargs):
        super(_Task, self).__init__()

        _add_task(tid, self)

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
        _pop_task(self.tid)

    def stop(self):
        self._stop = True


def start(tid, interval, repeat, exit_on_retval, func, *args, **kwargs):
    """
    Start a new task
    """
    LOG.info('start(tid=%s, interval=%s, repeat=%s, exit_on_retval=%s, '
             'func=%s, args=%s, kwargs=%s)', tid, interval, repeat,
             exit_on_retval, func.__name__, args, kwargs)

    t = _Task(tid, interval, repeat, exit_on_retval, func, *args, **kwargs)
    t.start()


def stop(tid):
    """
    Stop a running task
    """
    LOG.info('stop(tid=%s)', tid)

    t = _get_task(tid)
    if t is not None:
        t.stop()
