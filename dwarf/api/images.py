#!/usr/bin/python

import bottle
import logging
import threading

from tempfile import TemporaryFile

import dwarf.images as dwarf_images

from dwarf import exception
from dwarf import http

from dwarf import config
from dwarf import utils

CONF = config.CONFIG
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


class ImagesApiThread(threading.Thread):
    server = None

    def stop(self):
        # Stop the HTTP server
        try:
            self.server.stop()
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to stop Images API server')

    def run(self):
        """
        Images API thread worker
        """
        LOG.info('Starting images API worker')

        images = dwarf_images.Controller()
        app = bottle.Bottle()

        # GET:    glance image-list
        # HEAD:   glance image-show <image_id>
        # DELETE: glance image-delete <image_id>
        @app.route('/v1/images/<image_id>', method=('GET', 'HEAD', 'DELETE'))
        @app.route('//v1/images/<image_id>', method=('GET', 'HEAD', 'DELETE'))
        @exception.catchall
        def http_1(image_id):   # pylint: disable=W0612
            """
            Images actions
            """
            utils.show_request(bottle.request)

            # glance image-list
            if image_id == 'detail' and bottle.request.method == 'GET':
                return {'images': images.list()}

            # glance image-show <image_id>
            if image_id != 'detail' and bottle.request.method == 'HEAD':
                image = images.show(image_id)
                _add_header(image)
                return

            # glance image-delete <image_id>
            if image_id != 'detail' and bottle.request.method == 'DELETE':
                images.delete(image_id)
                return

            bottle.abort(400, 'Unable to handle request')

        # POST: glance image-create
        @app.route('/v1/images', method='POST')
        @app.route('//v1/images', method='POST')
        @exception.catchall
        def http_2():   # pylint: disable=W0612
            """
            Images actions
            """
            utils.show_request(bottle.request)

            # Parse the HTTP header
            image_md = {}
            for key in bottle.request.headers.keys():
                if key.lower().startswith('x-image-meta-'):
                    k = key.lower()[13:].replace('-', '_')
                    image_md[k] = bottle.request.headers[key]

            # glance image-create
            image_fh = _request_body(bottle.request)
            return {'image': images.add(image_fh, image_md)}

        # Start the HTTP server
        try:
            host = '127.0.0.1'
            port = CONF.images_api_port
            self.server = http.BaseHTTPServer(host=host, port=port)

            LOG.info('Images API server listening on %s:%s', host, port)
            bottle.run(app, server=self.server)
            LOG.info('Images API server shut down')
        except Exception:   # pylint: disable=W0703
            LOG.exception('Failed to start Images API server')
