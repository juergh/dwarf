#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import bottle
import json
import logging

from dwarf import api_server
from dwarf import config
from dwarf import exception
from dwarf import utils

from dwarf.compute.flavors import FLAVORS
from dwarf.compute.keypairs import KEYPAIRS
from dwarf.compute.images import IMAGES
from dwarf.compute.servers import SERVERS

CONF = config.Config()
LOG = logging.getLogger(__name__)


@exception.catchall
def _route_images_id(dummy_tenant_id, image_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/images/<image_id>
    Method: GET
    """
    utils.show_request(bottle.request)

    # nova image-list
    if image_id == 'detail':
        return {'images': IMAGES.list()}

    # nova image-show <image_id>
    return {'image': IMAGES.show(image_id)}


@exception.catchall
def _route_images(dummy_tenant_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/images
    Method: GET
    """
    utils.show_request(bottle.request)

    return {'images': IMAGES.list(detail=False)}


@exception.catchall
def _route_os_keypairs(dummy_tenant_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/os-keypairs
    Method: GET, POST
    """
    utils.show_request(bottle.request)

    # nova keypair-add
    if bottle.request.method == 'POST':
        body = json.load(bottle.request.body)
        return {'keypair': KEYPAIRS.add(body['keypair'])}

    # nova keypair-list
    return {'keypairs': KEYPAIRS.list()}


@exception.catchall
def _route_os_keypairs_name(dummy_tenant_id, keypair_name):
    """
    Route:  /v1.1/<dummy_tenant_id>/os-keypairs/<keypair_name>
    Method: DELETE
    """
    utils.show_request(bottle.request)

    KEYPAIRS.delete(keypair_name)


@exception.catchall
def _route_servers_id(dummy_tenant_id, server_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/servers/<server_id>
    Method: GET, DELETE
    """
    utils.show_request(bottle.request)

    # nova delete <server_id>
    if bottle.request.method == 'DELETE':
        SERVERS.delete(server_id)
        return

    # nova list
    if server_id == 'detail':
        return {'servers': SERVERS.list()}

    # nova show <server_id>
    return {'server': SERVERS.show(server_id)}


@exception.catchall
def _route_servers(dummy_tenant_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/servers
    Method: GET, POST
    """
    utils.show_request(bottle.request)

    # nova boot
    if bottle.request.method == 'POST':
        body = json.load(bottle.request.body)
        return {'server': SERVERS.boot(body['server'])}

    # nova list (no details)
    return {'servers': SERVERS.list(detail=False)}


@exception.catchall
def _route_servers_id_action(dummy_tenant_id, server_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/servers/<server_id>/action
    Method: POST
    """
    utils.show_request(bottle.request)

    body = json.load(bottle.request.body)

    # nova console-log
    if 'os-getConsoleOutput' in body:
        return {'output': SERVERS.console_log(server_id)}

    # nova reboot
    elif 'reboot' in body:
        hard = body['reboot']['type'].lower() == 'hard'
        SERVERS.reboot(server_id, hard)
        return

    bottle.abort(400)


@exception.catchall
def _route_flavors_id(dummy_tenant_id, flavor_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/flavors/<flavor_id>
    Method: GET, DELETE
    """
    utils.show_request(bottle.request)

    # nova flavor-delete <flavor_id>
    if bottle.request.method == 'DELETE':
        FLAVORS.delete(flavor_id)
        return

    # nova flavor-list
    if flavor_id == 'detail':
        return {'flavors': FLAVORS.list()}

    # nova flavor-show <flavor_id>
    return {'flavor': FLAVORS.show(flavor_id)}


@exception.catchall
def _route_flavors(dummy_tenant_id):
    """
    Route:  /v1.1/<dummy_tenant_id>/flavors
    Method: GET, POST
    """
    utils.show_request(bottle.request)

    # nova flavor-create
    if bottle.request.method == 'POST':
        body = json.load(bottle.request.body)
        return {'flavor': FLAVORS.create(body['flavor'])}

    # nova flavor-list (no details)
    return {'flavors': FLAVORS.list(detail=False)}


def _add_routes(app):
    """
    Add routes to the server app
    """
    # Images
    app.route('/v1.1/<dummy_tenant_id>/images/<image_id>',
              method='GET')(_route_images_id)
    app.route('/v1.1/<dummy_tenant_id>/images',
              method='GET')(_route_images)
    # Keypairs
    app.route('/v1.1/<dummy_tenant_id>/os-keypairs',
              method=('GET', 'POST'))(_route_os_keypairs)
    app.route('/v1.1/<dummy_tenant_id>/os-keypairs/<keypair_name>',
              method='DELETE')(_route_os_keypairs_name)
    # Servers
    app.route('/v1.1/<dummy_tenant_id>/servers/<server_id>',
              method=('GET', 'DELETE'))(_route_servers_id)
    app.route('/v1.1/<dummy_tenant_id>/servers',
              method=('GET', 'POST'))(_route_servers)
    app.route('/v1.1/<dummy_tenant_id>/servers/<server_id>/action',
              method='POST')(_route_servers_id_action)
    # Flavors
    app.route('/v1.1/<dummy_tenant_id>/flavors/<flavor_id>',
              method=('GET', 'DELETE'))(_route_flavors_id)
    app.route('/v1.1/<dummy_tenant_id>/flavors',
              method=('GET', 'POST'))(_route_flavors)


def ComputeApiServer():
    """
    Instantiate and configure the API server
    """
    server = api_server.ApiServer()

    server.name = 'Compute'
    server.host = '127.0.0.1'
    server.port = CONF.compute_api_port

    server.app = bottle.Bottle()
    _add_routes(server.app)

    return server
