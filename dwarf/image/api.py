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
import logging

from tempfile import TemporaryFile

from dwarf import api_server
from dwarf import config
from dwarf import exception
from dwarf import utils

from dwarf.image.images import IMAGES

CONF = config.Config()
LOG = logging.getLogger(__name__)


def _body_chunked(request):
    """
    Handle a chunked request body
    """
    def read_chunk(stream, length=None):
        if length:
            data = stream.read(length)
            if stream.read(2) != b'\r\n':
                raise ValueError("Malformed chunk in request")
            return data
        else:
            data = b''
            while True:
                b1 = stream.read(1)
                if not b1:
                    break
                if b1 == b'\r':
                    b2 = stream.read(1)
                    if not b2:
                        data += b1
                        break
                    if b2 == b'\n':
                        break
                    data += b1 + b2
                else:
                    data += b1
        return data

    stream = request.environ['wsgi.input']
    body = TemporaryFile(mode='w+b')
    while True:
        length = int(read_chunk(stream), 16)
        part = read_chunk(stream, length)
        if not part:
            break
        body.write(part)
    request.environ['wsgi.input'] = body
    body.seek(0)
    return body


def _request_body(request):
    """
    Wrapper for handling chunked request bodies
    """
    if (('Transfer-Encoding' in request.headers.keys() and
         request.headers['Transfer-Encoding'].lower() == 'chunked')):
        body = _body_chunked(request)
        body.seek(0)
        return body
    else:
        return request.body


def _add_header(metadata):
    # Hack: We can't use bottle's default add_header() method because it
    # replaces '_' with '-' in the header name
    func = bottle.response._headers.setdefault   # pylint: disable=W0212

    for (key, val) in metadata.iteritems():
        if key == 'properties':
            for (k, v) in val.iteritems():
                func('x-image-meta-property-%s' % k, []).append(str(v))
        else:
            func('x-image-meta-%s' % key, []).append(str(val))


def _from_headers(headers):
    # Extract the image metadata from the HTTP headers
    image_md = {}
    for key in headers.keys():
        if key.lower().startswith('x-image-meta-'):
            k = key.lower()[13:].replace('-', '_')
            image_md[k] = headers[key]
    return image_md


@exception.catchall
def _route_images_id(image_id):
    """
    Route:  /v1/images/<image_id>
    Method: GET, HEAD, DELETE, PUT
    """
    utils.show_request(bottle.request)

    # glance image-list
    if image_id == 'detail' and bottle.request.method == 'GET':
        return {'images': IMAGES.list()}

    # glance image-show <image_id>
    if image_id != 'detail' and bottle.request.method == 'HEAD':
        image = IMAGES.show(image_id)
        _add_header(image)
        return

    # glance image-delete <image_id>
    if image_id != 'detail' and bottle.request.method == 'DELETE':
        IMAGES.delete(image_id)
        return

    # glance image-update <image_id>
    if image_id != 'detail' and bottle.request.method == 'PUT':
        image_md = _from_headers(bottle.request.headers)
        return {'image': IMAGES.update(image_id, image_md)}

    bottle.abort(400, 'Unable to handle request')


@exception.catchall
def _route_images():
    """
    Route:  /v1/images
    Method: GET
    """
    utils.show_request(bottle.request)

    # Parse the HTTP header
    image_md = _from_headers(bottle.request.headers)

    # glance image-create
    image_fh = _request_body(bottle.request)
    return {'image': IMAGES.create(image_fh, image_md)}


def ImageApiServer():
    """
    Instantiate and configure the API server
    """
    server = api_server.ApiServer()

    server.name = 'Image'
    server.host = '127.0.0.1'
    server.port = CONF.image_api_port

    server.app = bottle.Bottle()
    server.app.route('/v1/images/<image_id>',
                     method=('GET', 'HEAD', 'DELETE', 'PUT'),
                     callback=_route_images_id)
    server.app.route('/v1/images',
                     method='POST',
                     callback=_route_images)

    return server
