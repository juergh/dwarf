#!/usr/bin/python

import bottle
import json
import threading

from dwarf import exception

from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG


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

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port

    def run(self):
        print("Starting auth API thread")

        app = bottle.Bottle()

        @app.post('/v2.0/tokens')
        @exception.catchall
        def http_tokens():   # pylint: disable=W0612
            """
            Tokens actions
            """
            if CONF.debug:
                utils.show_request(bottle.request)

            body = json.load(bottle.request.body)
            if 'auth' in body:
                return post_tokens_reply

            bottle.app(400)

        bottle.run(app, host='127.0.0.1', port=self.port)
