#!/usr/bin/env python
#
# Copyright (c) 2017 Hewlett Packard Enterprise Development, L.P.
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

VERSION_v2d0 = """{
    "id": "v2.0",
    "links": [
        {
            "href": "http://{{bind_host}}:{{identity_api_port}}/v2.0/",
            "rel": "self"
        }
    ],
    "media-types": [
        {
            "base": "application/json",
            "type": "application/vnd.openstack.identity-v2.0+json"
        }
    ],
    "status": "stable",
    "updated": "2014-04-17T00:00:00Z"
}"""


def show_version_v2d0():
    return {'version': utils.json_render(VERSION_v2d0, CONF.get_options())}


def list_versions():
    return {'versions': {'values': [show_version_v2d0()['version']]}}


# -----------------------------------------------------------------------------
# Authentication

TOKEN = """{
    "token": {
        "id": "0011223344556677",
        "expires": "2100-01-01T00:00:00-00:00",
        "tenant": {
            "id": "1000",
            "name": "dwarf-tenant"
        }
    },
    "user": {
        "id": "1000",
        "name": "dwarf-user",
        "roles": []
    },
    "serviceCatalog": [
        {
            "name": "Compute",
            "type": "compute",
            "endpoints": [
                {
                    "publicURL":
                    "http://{{bind_host}}:{{compute_api_port}}/v2.0",
                    "region": "dwarf-region"
                }
            ]
        },
        {
            "name": "Image",
            "type": "image",
            "endpoints": [
                {
                    "publicURL":
                    "http://{{bind_host}}:{{image_api_port}}",
                    "region": "dwarf-region"
                }
            ]
        },
        {
            "name": "Identity",
            "type": "identity",
            "endpoints": [
                {
                    "publicURL":
                    "http://{{bind_host}}:{{identity_api_port}}/v2.0",
                    "region": "dwarf-region"
                }
            ]
        }
    ]
}"""


def authenticate():
    return {'access': utils.json_render(TOKEN, CONF.get_options())}
