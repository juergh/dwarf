#!/usr/bin/python

from __future__ import print_function

import logging
import os

from hashlib import md5

from dwarf import db

from dwarf import config
from dwarf import utils

CONF = config.CONFIG
LOG = logging.getLogger(__name__)

IMAGES_INFO = ('checksum', 'created_at', 'container_format', 'disk_format',
               'id', 'is_public', 'location', 'min_disk', 'min_ram', 'name',
               'owner', 'properties', 'protected', 'updated_at', 'size',
               'status')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self):
        """
        List all images
        """
        LOG.info('list()')

        images = self.db.images.list()
        return utils.sanitize(images, IMAGES_INFO)

    def show(self, image_id):
        """
        Show image details
        """
        LOG.info('show(image_id=%s)', image_id)
        image = self.db.images.show(id=image_id)
        return utils.sanitize(image, IMAGES_INFO)

    def add(self, image_fh, image_md):
        """
        Add a new image
        """
        LOG.info('add(image_md=%s)', image_md)

        # Add the new image to the database
        image_md['status'] = 'SAVING'
        image = self.db.images.add(**image_md)
        image_id = image['id']

        # Copy the image and calculate its MD5 sum
        image_file = os.path.join(CONF.images_dir, image_id)
        with open(image_file, 'wb') as fh:
            d = md5()
            while True:
                buf = image_fh.read(4096)
                if not buf:
                    break
                d.update(buf)
                fh.write(buf)
        md5sum = d.hexdigest()

        # Update the image database entry
        image = self.db.images.update(id=image_id, checksum=md5sum,
                                      location='file://%s' % image_file,
                                      status='ACTIVE')

        return utils.sanitize(image, IMAGES_INFO)

    def delete(self, image_id):
        """
        Delete an image
        """
        LOG.info('delete(image_id=%s)', image_id)

        # Delete the image in the database
        self.db.images.delete(id=image_id)

        # Delete the image file
        image_file = os.path.join(CONF.images_dir, image_id)
        try:
            LOG.info('deleting image file %s', image_file)
            os.unlink(image_file)
        except OSError as ex:
            LOG.warn('failed to delete image %s (%s, %s)', image_file,
                     ex.errno, ex.strerror)
