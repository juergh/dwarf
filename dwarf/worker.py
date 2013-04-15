#!/usr/bin/python

from __future__ import print_function

import Queue
import threading

from dwarf.compute import compute


class WorkerThread(threading.Thread):

    def __init__(self, request_q):
        threading.Thread.__init__(self)
        self.request_q = request_q
        self.compute = compute.Controller(None)

    def run(self):
        print("Starting worker thread")

        while True:
            try:
                request = self.request_q.get(True, 1)

                print('worker.run: received request: service=%s, action=%s, '
                      'args=%s, kwargs=%s' %
                      (request['service'], request['action'], request['args'],
                       request['kwargs']))

                service = getattr(self, request['service'])
                action = getattr(service, request['action'])
                result = action(request['args'], request['kwargs'])

                request['result_q'].put(result)
                print('worker.run: sent result')

            except Queue.Empty:
                continue
