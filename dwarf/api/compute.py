#!/usr/bin/python

import bottle

from dwarf.api import base


class ComputeApiServerThread(base.ApiServerThread):

    def run(self):
        print("Starting compute server thread")

        app = bottle.Bottle()

        # nova image-list
        @app.route('/v1/<_tenant_id>/images/detail', method='GET')
        def images_detail(_tenant_id):   # pylint: disable=W0612
            result = self._do_request('compute', 'images')
            return result

        # nova image-show <image_id>
        @app.route('/v1/<_tenant_id>/images/<image_id>', method='GET')
        def images(_tenant_id, image_id):   # pylint: disable=W0612
            result = self._do_request('compute', 'image', image_id)
            return result

        # nova list
        @app.route('/v1/<_tenant_id>/servers/detail', method='GET')
        def server_detail(_tenant_id):   # pylint: disable=W0612
            result = self._do_request('compute', 'servers')
            return result

        bottle.run(app, host='127.0.0.1', port=self.port, quiet=self.quiet)
