#!/usr/bin/python

import bottle
import threading

from dwarf import exception
import dwarf.images as images


class ImagesApiThread(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.images = images.Controller()

    def run(self):
        print("Starting images server thread")

        app = bottle.Bottle()

        # GET:  glance index
        # HEAD: glance show <image_id>
        @app.get('/v1/images/detail')
        @app.route('/v1/images/<image_id>', method='HEAD')
        @exception.catchall
        def http_images(image_id=None):   # pylint: disable=W0612
            """
            Images actions
            """
            # glance index
            if not image_id and bottle.request.method == 'GET':
                return self.images.index()

            # glance show <image_id>
            if image_id and bottle.request.method == 'HEAD':
                return self.images.show(image_id)

            bottle.abort(400)

        bottle.run(app, host='127.0.0.1', port=self.port)
