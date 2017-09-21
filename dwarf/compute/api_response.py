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

from dwarf import config
from dwarf import utils

CONF = config.Config()

DETAILS = ('created_at', 'deleted', 'deleted_at', 'updated_at')


# -----------------------------------------------------------------------------
# Versions

VERSION_v2d0 = """{
    "id": "v2.0",
    "links": [
        {
            "href": "http://{{bind_host}}:{{bind_port}}/compute/v2.0/",
            "rel": "self"
        }
    ],
    "status": "CURRENT",
    "updated": "2016-05-11T00:00:00Z"
}"""


def show_version_v2d0():
    return {'version': utils.json_render(VERSION_v2d0, CONF.get_options())}


def list_versions():
    return {'versions': [show_version_v2d0()['version']]}


# -----------------------------------------------------------------------------
# Flavors

FLAVOR = """{
% if _details:
    "disk": "{{disk}}",
    "ram": "{{ram}}",
    "vcpus": "{{vcpus}}",
% end
    "id": "{{id}}",
    "links": [
        {
            "href": "",
            "rel": "self"
        }
    ],
    "name": "{{name}}"
}"""


def create_flavor(data):
    return {'flavor': utils.json_render(FLAVOR, data, _details=True)}


def list_flavors(data, details=True):
    return {'flavors': [utils.json_render(FLAVOR, d, _details=details)
                        for d in data]}


def show_flavor(data):
    return {'flavor': utils.json_render(FLAVOR, data, _details=True)}


# -----------------------------------------------------------------------------
# Keypairs

KEYPAIR = """{
% if _details:
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "updated_at": "{{updated_at}}",
    "id": "{{id}}",
% end
% if defined('private_key'):
    "private_key": "{{private_key}}",
% end
    "fingerprint": "{{fingerprint}}",
    "name": "{{name}}",
    "public_key": "{{public_key}}"
}"""


def create_keypair(data):
    return {'keypair': utils.json_render(KEYPAIR, data, _details=False)}


def list_keypairs(data):
    return {'keypairs': [utils.json_render(KEYPAIR, d, _details=False)
                         for d in data]}


def show_keypair(data):
    return {'keypair': utils.json_render(KEYPAIR, data, _details=True)}


# -----------------------------------------------------------------------------
# Servers

SERVER = """{
% if _details:
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "updated_at": "{{updated_at}}",
% end
    "addresses": {
        "private": [
            {
                "addr": "{{ip}}",
                "version": "4"
            }
        ]
    },
    "config_drive": "{{config_drive}}",
    "flavor": {
        "id": "{{flavor_id}}",
        "links": [
            {
                "href": "",
                "rel": "self"
            }
        ]
    },
    "id": "{{id}}",
    "image": {
        "id": "{{image_id}}",
        "links": [
            {
                "href": "",
                "rel": "self"
            }
        ]
    },
    "key_name": "{{key_name}}",
    "name": "{{name}}",
    "status": "{{status}}"
}"""


def create_server(data):
    return {'server': utils.json_render(SERVER, data, _details=True)}


def list_servers(data, details=True):
    return {'servers': [utils.json_render(SERVER, d, _details=details)
                        for d in data]}


def show_server(data):
    return {'server': utils.json_render(SERVER, data, _details=True)}


def show_console_log(data):
    return {'output': data}
