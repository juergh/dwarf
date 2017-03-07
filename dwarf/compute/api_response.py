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

from dwarf.utils import template

CONF = config.Config()

DETAILS = ('created_at', 'deleted', 'deleted_at', 'updated_at')


# -----------------------------------------------------------------------------
# Versions

VERSION_v2d0 = """{
    "id": "v2.0",
    "links": [
        {
            "href": "http://{{bind_host}}:{{compute_api_port}}/v2.0/",
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
    "fingerprint": "{{fingerprint}}",
    "name": "{{name}}",
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

SERVER = ('id', 'name')
SERVER_INFO = DETAILS + ('addresses', 'config_drive', 'flavor', 'id', 'image',
                         'key_name', 'name', 'status')
SERVER_LINKS = {"links": [{"href": "", "rel": "self"}]}


def servers_create(data):
    return {"server": template(SERVER_INFO, data)}


def servers_console_log(data):
    return {'output': data}


def servers_list(data, details=True):
    if details:
        return {"servers": template(SERVER_INFO, data)}
    else:
        return {"servers": template(SERVER, data)}


def servers_show(data):
    return {"server": template(SERVER_INFO, data)}
