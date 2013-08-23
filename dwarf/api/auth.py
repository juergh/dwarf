#!/usr/bin/python

import bottle
import json
import logging
import threading

from dwarf import exception
from dwarf import http

from dwarf.common import config
from dwarf.common import utils

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
            "publicURL": "http://127.0.0.1:8774/v1/1000",
            "region": "dwarf-region",
            "versionId": "1.1",
            "versionInfo": "http://127.0.0.1:8774/v1.1",
            "versionList": "http://127.0.0.1:8774"
    }]
}


service_image = {
    "name": "Image Management",
    "type": "image",
    "endpoints": [{
            "tenantId": "1000",
            "publicURL": "http://127.0.0.1:9292/v1.0",
            "region": "dwarf-region",
            "versionId": "1.0",
            "versionInfo": "http://127.0.0.1:9292/v1.0",
            "versionList": "http://127.0.0.1:9292"
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


class AuthApiThread(threading.Thread):
    server = None

    def stop(self):
        self.server.stop()

    def run(self):
        """
        Auth API thread worker
        """
        LOG.info('Starting auth API worker')

        app = bottle.Bottle()

        @app.post('/v2.0/tokens')
        @exception.catchall
        def http_1():   # pylint: disable=W0612
            """
            Tokens actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            body = json.load(bottle.request.body)
            if 'auth' in body:
                return post_tokens_reply

            bottle.app(400)

        host = '127.0.0.1'
        port = CONF.auth_api_port
        self.server = http.BaseHTTPServer(host=host, port=port)

        LOG.info('Auth API server listening on %s:%s', host, port)
        bottle.run(app, server=self.server)
        LOG.info('Auth API server shut down')
