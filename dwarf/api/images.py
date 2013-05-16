#!/usr/bin/python

import bottle
import threading

from dwarf import exception
import dwarf.images as images

from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG


def add_header(metadata):
    # Hack: We can't use bottle's default add_header() method because it
    # replaces '_' with '-' in the header name
    func = bottle.response._headers.setdefault   # pylint: disable=W0212

    for (key, val) in metadata.iteritems():
        if key == 'properties':
            for (k, v) in val.iteritems():
                func('x-image-meta-property-%s' % k, []).append(str(v))
        else:
            func('x-image-meta-%s' % key, []).append(str(val))


class ImagesApiThread(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.images = images.Controller()

    def run(self):
        print("Starting images server thread")

        app = bottle.Bottle()

        # GET:    glance index
        # HEAD:   glance show <image_id>
        # DELETE: glance delete <image_id>
        @app.route('/v1/images/<image_id>', method=('GET', 'HEAD', 'DELETE'))
        @exception.catchall
        def http_images(image_id):   # pylint: disable=W0612
            """
            Images actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # glance index
            if image_id == 'detail' and bottle.request.method == 'GET':
                return {'images': self.images.list()}

            # glance show <image_id>
            if image_id != 'detail' and bottle.request.method == 'HEAD':
                image = self.images.show(image_id)
                add_header(image)
                return

            # glance delete <image_id>
            if image_id != 'detail' and bottle.request.method == 'DELETE':
                self.images.delete(image_id)
                return

            bottle.abort(400, 'Unable to handle request')

        # POST: glance add
        @app.route('/v1/images', method='POST')
        @exception.catchall
        def http_images2():   # pylint: disable=W0612
            """
            Images actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # Parse the HTTP header
            image_md = {}
            for key in bottle.request.headers.keys():
                if key.lower().startswith('x-image-meta-'):
                    k = key.lower()[13:].replace('-', '_')
                    image_md[k] = bottle.request.headers[key]

            # glance add
            image_fh = bottle.request.body
            return {'image': self.images.add(image_fh, image_md)}

        bottle.run(app, host='127.0.0.1', port=self.port)
