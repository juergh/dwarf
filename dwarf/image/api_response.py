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


# -----------------------------------------------------------------------------
# Versions

VERSION_v2 = """{
    "id": "v2",
    "links": [
        {
            "href": "http://{{bind_host}}:{{image_api_port}}/v2/",
            "rel": "self"
        }
    ],
    "status": "CURRENT",
    "updated": "2016-05-11T00:00:00Z"
}"""


def list_versions():
    return {'versions': [utils.json_render(VERSION_v2, CONF.get_options())]}


# -----------------------------------------------------------------------------
# Images

IMAGE = """{
    "checksum": "{{checksum}}",
    "container_format": "{{container_format}}",
    "created_at": "{{created_at}}",
    "disk_format": "{{disk_format}}",
    "file": "{{file}}",
    "id": "{{id}}",
    "min_disk": "{{min_disk}}",
    "min_ram": "{{min_ram}}",
    "name": "{{name}}",
    "owner": "{{owner}}",
    "protected": "{{protected}}",
    "size": "{{size}}",
    "status": "{{status}}",
    "updated_at": "{{updated_at}}",
    "visibility": "{{visibility}}"
% end
}"""


def create_image(data):
    return utils.json_render(IMAGE, data)


def list_images(data):
    return {'images': [utils.json_render(IMAGE, d) for d in data]}


def show_image(data):
    return utils.json_render(IMAGE, data)


def update_image(data):
    return utils.json_render(IMAGE, data)


# -----------------------------------------------------------------------------
# Schemas

IMAGE_SCHEMA = {
    'name': 'image',
    'properties': {
        'container_format': {},
        'disk_format': {},
        'min_disk': {},
        'min_ram': {},
        'name': {},
        'owner': {},
        'protected': {},
        'visibility': {},
    }
}


def show_image_schema():
    return IMAGE_SCHEMA


# -----------------------------------------------------------------------------
# Metadata definitions

def list_metadefs():
    return []
