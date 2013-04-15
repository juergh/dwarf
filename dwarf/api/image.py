#!/usr/bin/python

import bottle
import Queue
import threading


class ImageServerThread(threading.Thread):

    def __init__(self, port, request_q, quiet=False):
        threading.Thread.__init__(self)
        self.port = port
        self.request_q = request_q
        self.quiet = quiet
        self.result_q = Queue.Queue()

    def run(self):
        print("Starting image server thread")

        app = bottle.Bottle()

        # glance index
        @app.route('/v1/images/detail', method='GET')
        def images_detail():   # pylint: disable=W0612
            return {'images': []}

        # glance show <image_id>
        @app.route('/v1/images/<_image_id>', method='HEAD')
        def images_id(_image_id):   # pylint: disable=W0612
            return {'image': {}}

        bottle.run(app, host='127.0.0.1', port=self.port, quiet=self.quiet)
