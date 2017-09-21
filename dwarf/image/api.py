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

from dwarf.image import api_response
from dwarf.image import images

CONF = config.Config()
LOG = logging.getLogger(__name__)

IMAGES = images.Controller()


# -----------------------------------------------------------------------------
# Bottle API routes

@exception.catchall
def _route_versions():
    """
    Route:  /image, /image/versions
    Method: GET
    """
    utils.show_request(bottle.request)

    bottle.response.status = 300
    return api_response.list_versions()


@exception.catchall
def _route_images():
    """
    Route:  /image/v2/images
    Method: GET, POST
    """
    utils.show_request(bottle.request)

    # glance image-create
    if bottle.request.method == 'POST':
        bottle.response.status = 201
        image_md = json.load(bottle.request.body)
        return api_response.create_image(IMAGES.create(image_md))

    # glance image-list
    return api_response.list_images(IMAGES.list())


@exception.catchall
def _route_images_id(image_id):
    """
    Route:  /image/v2/images/<image_id>
    Method: GET, DELETE, PATCH
    """
    utils.show_request(bottle.request)

    # glance image-delete
    if bottle.request.method == 'DELETE':
        bottle.response.status = 204
        IMAGES.delete(image_id)
        return

    # glance image-update
    if bottle.request.method == 'PATCH':
        image_ops = json.load(bottle.request.body)
        return api_response.update_image(IMAGES.update(image_id, image_ops))

    # glance image-show
    return api_response.show_image(IMAGES.show(image_id))


@exception.catchall
def _route_images_id_file(image_id):
    """
    Route:  /image/v2/images/<image_id>/file
    Method: PUT
    """
    utils.show_request(bottle.request)

    # glance image-upload
    bottle.response.status = 204
    image_fh = bottle.request.body
    IMAGES.upload(image_id, image_fh)
    return


@exception.catchall
def _route_schemas_image():
    """
    Route:  /image/v2/schemas/image
    Method: GET
    """
    utils.show_request(bottle.request)

    return api_response.show_image_schema()


@exception.catchall
def _route_schemas_metadefs(_metadef):
    """
    Route:  /image/v2/schemas/metadefs/<_metadef>
    Method: GET
    """
    utils.show_request(bottle.request)

    return api_response.list_metadefs()


# -----------------------------------------------------------------------------
# Image API exports

def set_routes(app):
    app.route(('/image', '/image/versions'),
              method='GET',
              callback=_route_versions)
    app.route('/image/v2/images',
              method=('GET', 'POST', ),
              callback=_route_images)
    app.route('/image/v2/images/<image_id>',
              method=('GET', 'DELETE', 'PATCH'),
              callback=_route_images_id)
    app.route('/image/v2/images/<image_id>/file',
              method=('PUT'),
              callback=_route_images_id_file)
    app.route('/image/v2/schemas/image',
              method='GET',
              callback=_route_schemas_image)
    app.route('/image/v2/schemas/metadefs/<_metadef>',
              method='GET',
              callback=_route_schemas_metadefs)


def setup():
    pass


def teardown():
    pass
