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
# Images API responses

IMAGE = DETAILS + ('checksum', 'container_format', 'disk_format', 'id',
                   'is_public', 'location', 'min_disk', 'min_ram', 'name',
                   'owner', 'protected', 'size', 'status')
IMAGE_PROPERTIES = {'properties': {}}


def images_create(data):
    return {"image": template(IMAGE, data, add=IMAGE_PROPERTIES)}


def images_list(data):
    return {"images": template(IMAGE, data, add=IMAGE_PROPERTIES)}


def images_update(data):
    return {"image": template(IMAGE, data, add=IMAGE_PROPERTIES)}
