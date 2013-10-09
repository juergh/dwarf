#!/usr/bin/python

import bottle
import json
import logging
import threading

from dwarf import compute as dwarf_compute
from dwarf import exception
from dwarf import http

from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG
LOG = logging.getLogger(__name__)


class ComputeApiThread(threading.Thread):
    server = None

    def stop(self):
        # Stop the HTTP server
        try:
            self.server.stop()
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to stop Compute API server')

    def run(self):
        """
        Compute API thread worker
        """
        LOG.info('Starting compute API worker')

        compute = dwarf_compute.Controller()
        app = bottle.Bottle()

        # GET: nova image-list
        # GET: nova image-show <image_id>
        @app.get('/v1.1/<dummy_tenant_id>/images/<image_id>')
        @exception.catchall
        def http_1(dummy_tenant_id, image_id):   # pylint: disable=W0612
            """
            Images actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova image-list
            if image_id == 'detail':
                return {'images': compute.images.list()}

            # nova image-show <image_id>
            else:
                return {'image': compute.images.show(image_id)}

        # GET:  nova keypair-list
        # POST: nova keypair-add
        @app.get('/v1.1/<dummy_tenant_id>/os-keypairs')
        @app.post('/v1.1/<dummy_tenant_id>/os-keypairs')
        @exception.catchall
        def http_2(dummy_tenant_id):   # pylint: disable=W0612
            """
            Keypairs actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova keypair-list
            if bottle.request.method == 'GET':
                return {'keypairs': compute.keypairs.list()}

            # nova keypair-add
            if bottle.request.method == 'POST':
                body = json.load(bottle.request.body)
                return {'keypair': compute.keypairs.add(body['keypair'])}

            bottle.abort(400)

        @app.delete('/v1.1/<dummy_tenant_id>/os-keypairs/<keypair_name>')
        @exception.catchall
        def http_3(dummy_tenant_id, keypair_name):   # pylint: disable=W0612
            """
            Keypair actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            compute.keypairs.delete(keypair_name)

        # GET: nova list
        # GET: nova show <server_id>
        # DELTET: nova delete <server id>
        @app.get('/v1.1/<dummy_tenant_id>/servers/<server_id>')
        @app.delete('/v1.1/<dummy_tenant_id>/servers/<server_id>')
        @exception.catchall
        def http_4(dummy_tenant_id, server_id):   # pylint: disable=W0612
            """
            Servers actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova delete <server_id>
            if bottle.request.method == 'DELETE':
                compute.servers.delete(server_id)
                return

            # nova list
            if server_id == 'detail':
                return {'servers': compute.servers.list()}

            # nova show <server_id>
            else:
                return {'server': compute.servers.show(server_id)}

        # POST: nova boot
        @app.post('/v1.1/<dummy_tenant_id>/servers')
        @exception.catchall
        def http_5(dummy_tenant_id):   # pylint: disable=W0612
            """
            Servers actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova boot
            body = json.load(bottle.request.body)
            return {'server': compute.servers.boot(body['server'])}

        # POST: nova console-log
        # POST: nova reboot
        @app.post('/v1.1/<dummy_tenant_id>/servers/<server_id>/action')
        @exception.catchall
        def http_6(dummy_tenant_id, server_id):   # pylint: disable=W0612
            """
            Servers actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            body = json.load(bottle.request.body)

            # nova console-log
            if 'os-getConsoleOutput' in body:
                return {'output': compute.servers.console_log(server_id)}

            # nova reboot
            elif 'reboot' in body:
                hard = body['reboot']['type'].lower() == 'hard'
                compute.servers.reboot(server_id, hard)
                return

            bottle.abort(400)

        # GET: nova flavor list
        # GET: nova flavor show <flavor_id>
        @app.get('/v1.1/<dummy_tenant_id>/flavors/<flavor_id>')
        @exception.catchall
        def http_7(dummy_tenant_id, flavor_id):   # pylint: disable=W0612
            """
            Flavors actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            # nova flavor-list
            if flavor_id == 'detail':
                return {'flavors': compute.flavors.list()}

            # nova flavor-show <flavor_id>
            else:
                return {'flavor': compute.flavors.show(flavor_id)}

        # Start the HTTP server
        try:
            host = '127.0.0.1'
            port = CONF.compute_api_port
            self.server = http.BaseHTTPServer(host=host, port=port)

            LOG.info('Compute API server listening on %s:%s', host, port)
            bottle.run(app, server=self.server)
            LOG.info('Compute API server shut down')
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to start Compute API server')
