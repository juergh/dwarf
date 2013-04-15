#!/usr/bin/python

import bottle
import json

from dwarf.api import base


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


class AuthApiServerThread(base.ApiServerThread):

    def run(self):
        print("Starting auth server thread")

        app = bottle.Bottle()

        @app.route('/v2.0/tokens', method='POST')
        def tokens():   # pylint: disable=W0612
            body = json.load(bottle.request.body)
            if 'auth' in body:
                return post_tokens_reply
            bottle.abort(400)

        bottle.run(app, host='127.0.0.1', port=self.port, quiet=self.quiet)
