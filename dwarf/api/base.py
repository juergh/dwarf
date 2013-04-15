#!/usr/bin/python

import Queue
import threading


class ApiServerThread(threading.Thread):

    def __init__(self, port, request_q=None, quiet=False):
        threading.Thread.__init__(self)
        self.port = port
        self.request_q = request_q
        self.quiet = quiet
        self.result_q = Queue.Queue()

    def _do_request(self, service, action, *args, **kwargs):
        request = {
            'result_q': self.result_q,
            'service': service,
            'action': action,
            'args': args,
            'kwargs': kwargs
        }
        self.request_q.put(request)
        return self.result_q.get()
