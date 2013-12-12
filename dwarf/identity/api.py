#!/usr/bin/python

import bottle
import json
import logging
import threading

from dwarf import exception
from dwarf import http

from dwarf import config
from dwarf import utils

CONF = config.CONFIG
LOG = logging.getLogger(__name__)


token = {
    "id": "0011223344556677",
    "expires": "2100-01-01T00:00:00-00:00",
    "tenant": {
        "id": "1000",
        "name": "dwarf-tenant"
    }
}


user = {
    "id": "1000",
    "name": "dwarf-user",
    "roles": []
}


service_compute = {
    "name": "Compute",
    "type": "compute",
    "endpoints": [{
            "tenantId": "1000",
            "publicURL": "http://127.0.0.1:%s/v1.1/1000" %
            CONF.compute_api_port,
            "region": "dwarf-region",
            "versionId": "1.1",
            "versionInfo": "http://127.0.0.1:%s/v1.1" % CONF.compute_api_port,
            "versionList": "http://127.0.0.1:%s" % CONF.compute_api_port
    }]
}


service_image = {
    "name": "Image Management",
    "type": "image",
    "endpoints": [{
            "tenantId": "1000",
            "publicURL": "http://127.0.0.1:%s/v1.0" % CONF.image_api_port,
            "region": "dwarf-region",
            "versionId": "1.0",
            "versionInfo": "http://127.0.0.1:%s/v1.0" % CONF.image_api_port,
            "versionList": "http://127.0.0.1:%s" % CONF.image_api_port
    }]
}


post_tokens_reply = {
    "access": {
        "token": token,
        "user": user,
        "serviceCatalog": [
            service_compute,
            service_image
        ]
    }
}


class IdentityApiThread(threading.Thread):
    server = None

    def stop(self):
        # Stop the HTTP server
        try:
            self.server.stop()
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to stop Identity API server')

    def run(self):
        """
        Identity API thread worker
        """
        LOG.info('Starting Identity API worker')

        app = bottle.Bottle()

        #
        # Tokens API
        #

        @app.post('/v2.0/tokens')
        @exception.catchall
        def tokens_1():   # pylint: disable=W0612
            """
            Tokens actions
            """
            utils.show_request(bottle.request)

            body = json.load(bottle.request.body)
            if 'auth' in body:
                return post_tokens_reply

            bottle.app(400)

        #
        # Start the HTTP server
        #

        try:
            host = '127.0.0.1'
            port = CONF.identity_api_port
            self.server = http.BaseHTTPServer(host=host, port=port)

            LOG.info('Identity API server listening on %s:%s', host, port)
            bottle.run(app, server=self.server)
            LOG.info('Identity API server shut down')
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to start Identity API server')
