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

_TASKS = {}


class _Task(Thread):

    def __init__(self, tid, interval, repeat, func, *args, **kwargs):
        super(_Task, self).__init__()

        self.tid = tid
        self.interval = interval
        self.repeat = repeat

        self.func = func
        self.args = args
        self.kwargs = kwargs

        self._stop = False

        _TASKS[tid] = self
        self.start()

    def run(self):
        for dummy in range(self.repeat):
            if self._stop:
                break
            retval = self.func(*self.args, **self.kwargs)
            if retval is not None:
                break
            time.sleep(self.interval)
        _TASKS.pop(self.tid, None)

    def stop(self):
        self._stop = True


def start(tid, interval, repeat, func, *args, **kwargs):
    """
    Start a new task
    """
    LOG.info('start(tid=%s, interval=%s, repeat=%s, func=%s, args=%s, '
             'kwargs=%s)', tid, interval, repeat, func.__name__, args, kwargs)

    _Task(tid, interval, repeat, func, *args, **kwargs)


def stop(tid):
    """
    Stop a running task
    """
    LOG.info('stop(tid=%s)', tid)

    t = _TASKS.get(tid, None)
    if t is not None:
        t.stop()


def stop_all(wait=False):
    """
    Stop all running tasks
    """
    LOG.info('stop_all()')

    for tid in _TASKS:
        stop(tid)

    if wait:
        while _TASKS:
            time.sleep(0.5)
