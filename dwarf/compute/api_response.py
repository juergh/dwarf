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

from dwarf.utils import template

DETAILS = ('created_at', 'deleted', 'deleted_at', 'updated_at')

# -----------------------------------------------------------------------------
# Flavors API responses

FLAVOR = ('id', 'name')
FLAVOR_INFO = FLAVOR + ('disk', 'ram', 'vcpus')
FLAVOR_LINKS = {"links": [{"href": "", "rel": "self"}]}


def flavors_create(data):
    return {"flavor": template(FLAVOR_INFO, data, add=FLAVOR_LINKS)}


def flavors_list(data, details=True):
    if details:
        return {"flavors": template(FLAVOR_INFO, data, add=FLAVOR_LINKS)}
    else:
        return {"flavors": template(FLAVOR, data, add=FLAVOR_LINKS)}


def flavors_show(data):
    return {"flavor": template(FLAVOR_INFO, data, add=FLAVOR_LINKS)}


# -----------------------------------------------------------------------------
# Images API responses

IMAGE = ('id', 'name')
IMAGE_INFO = DETAILS + IMAGE + ('is_public', 'size', 'status', 'location')
IMAGE_LINKS = {"links": [{"href": "", "rel": "self"}]}


def images_list(data, details=True):
    if details:
        return {"images": template(IMAGE_INFO, data, add=IMAGE_LINKS)}
    else:
        return {"images": template(IMAGE, data, add=IMAGE_LINKS)}


def images_show(data):
    return {"image": template(IMAGE_INFO, data, add=IMAGE_LINKS)}


# -----------------------------------------------------------------------------
# Keypairs API responses

KEYPAIR = ('fingerprint', 'name', 'public_key')
KEYPAIR_INFO = DETAILS + KEYPAIR + ('id', )


def keypairs_add(data):
    return {"keypair": template(KEYPAIR, data, add_if_present='private_key')}


def keypairs_list(data):
    return {"keypairs": template(KEYPAIR, data)}


def keypairs_show(data):
    return {"keypair": template(KEYPAIR_INFO, data)}


# -----------------------------------------------------------------------------
# Servers API responses

SERVER = ('id', 'name')
SERVER_INFO = DETAILS + ('addresses', 'config_drive', 'flavor', 'id', 'image',
                         'key_name', 'name', 'status')
SERVER_LINKS = {"links": [{"href": "", "rel": "self"}]}


def servers_boot(data):
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
