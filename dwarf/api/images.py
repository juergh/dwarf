#!/usr/bin/python

import bottle

from dwarf.api import base


class ImagesApiServerThread(base.ApiServerThread):

    def run(self):
        print("Starting images server thread")

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
