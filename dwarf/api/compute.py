#!/usr/bin/python

import bottle
import json
import logging
import threading

from wsgiref.simple_server import WSGIRequestHandler

from dwarf import compute
from dwarf import exception
from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG
LOG = logging.getLogger(__name__)


class ComputeApiRequestHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        LOG.info(fmt, *args)


class ComputeApiThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.compute = compute.Controller()

    def run(self):   # pylint: disable=R0912
        LOG.info('Starting compute API thread')

        app = bottle.Bottle()

        # GET: nova image-list
        # GET: nova image-show <image_id>
#        @app.get('/v1/<_tenant_id>/images/detail')
        @app.get('/v1/<_tenant_id>/images/<image_id>')
        @exception.catchall
        def http_images(_tenant_id, image_id):   # pylint: disable=W0612
            """
            Images actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

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
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova keypair-list
            if bottle.request.method == 'GET':
                return {'keypairs': self.compute.keypairs.list()}

            # nova keypair-add
            if bottle.request.method == 'POST':
                body = json.load(bottle.request.body)
                return {'keypair': self.compute.keypairs.add(body['keypair'])}

            bottle.abort(400)

        @app.delete('/v1/<_tenant_id>/os-keypairs/<keypair_name>')
        @exception.catchall
        def http_keypair(_tenant_id, keypair_name):   # pylint: disable=W0612
            """
            Keypair actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            self.compute.keypairs.delete(keypair_name)

        # GET: nova list
        # GET: nova show <server_id>
#        @app.get('/v1/<_tenant_id>/servers/detail')
        @app.get('/v1/<_tenant_id>/servers/<server_id>')
        @app.delete('/v1/<_tenant_id>/servers/<server_id>')
        @exception.catchall
        def http_servers(_tenant_id, server_id):   # pylint: disable=W0612
            """
            Servers actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova delete <server_id>
            if bottle.request.method == 'DELETE':
                self.compute.servers.delete(server_id)
                return

            # nova list
            if server_id == 'detail':
                return {'servers': self.compute.servers.list()}

            # nova show <server_id>
            else:
                return {'server': self.compute.servers.show(server_id)}

        # POST: nova boot
        @app.post('/v1/<_tenant_id>/servers')
        @exception.catchall
        def http_servers2(_tenant_id):   # pylint: disable=W0612
            """
            Servers actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova boot
            body = json.load(bottle.request.body)
            return {'server': self.compute.servers.boot(body['server'])}

        # GET: nova flavor list
        # GET: nova flavor show <flavor_id>
#        @app.get('/v1/<_tenant_id>/flavors/detail')
        @app.get('/v1/<_tenant_id>/flavors/<flavor_id>')
        @exception.catchall
        def http_flavors(_tenant_id, flavor_id):   # pylint: disable=W0612
            """
            Flavors actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova flavor-list
            if flavor_id == 'detail':
                return {'flavors': self.compute.flavors.list()}

            # nova flavor-show <flavor_id>
            else:
                return {'flavor': self.compute.flavors.show(flavor_id)}

        bottle.run(app, host='127.0.0.1', port=self.port,
                   handler_class=ComputeApiRequestHandler)
