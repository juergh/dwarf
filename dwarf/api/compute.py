#!/usr/bin/python

import bottle
import json
import threading

from dwarf import compute
from dwarf import exception


class ComputeApiThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.compute = compute.Controller()

    def run(self):
        print("Starting compute API thread")

        app = bottle.Bottle()

        # GET: nova image-list
        # GET: nova image-show <image_id>
        @app.get('/v1/<_tenant_id>/images/detail')
        @app.get('/v1/<_tenant_id>/images/<image_id>')
        @exception.catchall
        def http_images(_tenant_id, image_id):   # pylint: disable=W0612
            """
            Images actions
            """
            print(image_id)
            # nova image-list
            if image_id == 'detail':
                return {'images': self.compute.images.list()}

            # nova image-show <image_id>
            else:
                return {'image': self.compute.images.show(image_id)}

        # GET:  nova keypair-list
        # POST: nova keypair-add
        @app.get('/v1/<_tenant_id>/os-keypairs')
        @app.post('/v1/<_tenant_id>/os-keypairs')
        @exception.catchall
        def http_keypairs(_tenant_id):   # pylint: disable=W0612
            """
            Keypairs actions
            """
            # nova keypair-list
            if bottle.request.method == 'GET':
                return {'keypairs': self.compute.keypairs.list()}

            # nova keypair-add
            if bottle.request.method == 'POST':
                body = json.load(bottle.request.body)
                return {'keypair': self.compute.keypairs.add(body['keypair'])}

            bottle.abort(400)

        @app.delete('/v1/<_tenant_id>/os-keypairs/<keypair>')
        @exception.catchall
        def http_keypair(_tenant_id, keypair_name):   # pylint: disable=W0612
            """
            Keypair actions
            """
            self.compute.keypairs.delete(keypair_name)

        # GET: nova list
        @app.get('/v1/<_tenant_id>/servers/detail')
        @exception.catchall
        def http_servers(_tenant_id):   # pylint: disable=W0612
            """
            Servers actions
            """
            return {'servers': self.compute.servers.list()}

        bottle.run(app, host='127.0.0.1', port=self.port)
