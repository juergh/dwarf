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

from dwarf import config
from dwarf import exception
from dwarf import utils

from dwarf.compute import api_response
from dwarf.compute import flavors
from dwarf.compute import keypairs
from dwarf.compute import servers

CONF = config.Config()
LOG = logging.getLogger(__name__)

FLAVORS = flavors.Controller()
KEYPAIRS = keypairs.Controller()
SERVERS = servers.Controller()


# -----------------------------------------------------------------------------
# Bottle Versions API routes

@exception.catchall
def _route_versions():
    """
    Routes: /compute
    Method: GET
    """
    utils.show_request(bottle.request)

    bottle.response.status = 300
    return api_response.list_versions()


@exception.catchall
def _route_version():
    """
    Routes: /compute/v2.0
    Method: GET
    """
    utils.show_request(bottle.request)

    return api_response.show_version_v2d0()


# -----------------------------------------------------------------------------
# Bottle Flavors API routes

@exception.catchall
def _route_flavors_id(flavor_id):
    """
    Route:  /compute/v2.0/flavors/<flavor_id>
    Method: GET, DELETE
    """
    utils.show_request(bottle.request)

    # nova flavor-delete <flavor_id>
    if bottle.request.method == 'DELETE':
        FLAVORS.delete(flavor_id)
        return

    # nova flavor-list
    if flavor_id == 'detail':
        return api_response.list_flavors(FLAVORS.list(), details=True)

    # nova flavor-show <flavor_id>
    return api_response.show_flavor(FLAVORS.show(flavor_id))


@exception.catchall
def _route_flavors():
    """
    Route:  /compute/v2.0/flavors
    Method: GET, POST
    """
    utils.show_request(bottle.request)

    # nova flavor-create
    if bottle.request.method == 'POST':
        body = json.load(bottle.request.body)
        return api_response.create_flavor(FLAVORS.create(body['flavor']))

    # nova flavor-list (no details)
    return api_response.list_flavors(FLAVORS.list(), details=False)


# -----------------------------------------------------------------------------
# Bottle Keypair API routes

@exception.catchall
def _route_os_keypairs():
    """
    Route:  /compute/v2.0/os-keypairs
    Method: GET, POST
    """
    utils.show_request(bottle.request)

    # nova keypair-add
    if bottle.request.method == 'POST':
        body = json.load(bottle.request.body)
        return api_response.create_keypair(KEYPAIRS.create(body['keypair']))

    # nova keypair-list
    return api_response.list_keypairs(KEYPAIRS.list())


@exception.catchall
def _route_os_keypairs_name(keypair_name):
    """
    Route:  /compute/v2.0/os-keypairs/<keypair_name>
    Method: DELETE, GET
    """
    utils.show_request(bottle.request)

    # nova keypair-delete
    if bottle.request.method == 'DELETE':
        KEYPAIRS.delete(keypair_name)
        return

    # nova keypair-show
    return api_response.show_keypair(KEYPAIRS.show(keypair_name))


# -----------------------------------------------------------------------------
# Bottle Servers API routes

@exception.catchall
def _route_servers_id(server_id):
    """
    Route:  /compute/v2.0/servers/<server_id>
    Method: GET, DELETE
    """
    utils.show_request(bottle.request)

    # nova delete <server_id>
    if bottle.request.method == 'DELETE':
        SERVERS.delete(server_id)
        return

    # nova list
    if server_id == 'detail':
        return api_response.list_servers(SERVERS.list(), details=True)

    # nova show <server_id>
    return api_response.show_server(SERVERS.show(server_id))


@exception.catchall
def _route_servers():
    """
    Route:  /compute/v2.0/servers
    Method: GET, POST
    """
    utils.show_request(bottle.request)

    # nova boot
    if bottle.request.method == 'POST':
        body = json.load(bottle.request.body)
        return api_response.create_server(SERVERS.create(body['server']))

    # nova list (no details)
    return api_response.list_servers(SERVERS.list(), details=False)


@exception.catchall
def _route_servers_id_action(server_id):
    """
    Route:  /compute/v2.0/servers/<server_id>/action
    Method: POST
    """
    utils.show_request(bottle.request)

    body = json.load(bottle.request.body)

    # nova console-log
    if 'os-getConsoleOutput' in body:
        return api_response.show_console_log(SERVERS.console_log(server_id))

    # nova start
    elif 'os-start' in body:
        SERVERS.start(server_id)
        return

    # nova stop
    elif 'os-stop' in body:
        SERVERS.stop(server_id)
        return

    # nova reboot
    elif 'reboot' in body:
        hard = body['reboot']['type'].lower() == 'hard'
        SERVERS.reboot(server_id, hard)
        return

    raise exception.BadRequest(reason='Unsupported request')


# -----------------------------------------------------------------------------
# Compute API exports

def set_routes(app):
    app.route('/compute',
              method='GET',
              callback=_route_versions)
    app.route('/compute/v2.0',
              method='GET',
              callback=_route_version)
    app.route('/compute/v2.0/os-keypairs',
              method=('GET', 'POST'),
              callback=_route_os_keypairs)
    app.route('/compute/v2.0/os-keypairs/<keypair_name>',
              method=('DELETE', 'GET'),
              callback=_route_os_keypairs_name)
    app.route('/compute/v2.0/servers/<server_id>',
              method=('GET', 'DELETE'),
              callback=_route_servers_id)
    app.route('/compute/v2.0/servers',
              method=('GET', 'POST'),
              callback=_route_servers)
    app.route('/compute/v2.0/servers/<server_id>/action',
              method='POST',
              callback=_route_servers_id_action)
    app.route('/compute/v2.0/flavors/<flavor_id>',
              method=('GET', 'DELETE'),
              callback=_route_flavors_id)
    app.route('/compute/v2.0/flavors',
              method=('GET', 'POST'),
              callback=_route_flavors)


def setup():
    SERVERS.setup()


def teardown():
    SERVERS.teardown()
