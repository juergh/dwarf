#!/usr/bin/python

from __future__ import print_function

import logging
import os

from hashlib import md5

from dwarf import db
from dwarf import exception

from dwarf.common import config
from dwarf.common import utils

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

        # Read the image data, store it in a temp location and calculate the
        # md5 sum
        tmp_file = '%s/tmp' % CONF.images_dir
        with open(tmp_file, 'wb') as target:
            d = md5()
            while True:
                buf = image_fh.read(4096)
                if not buf:
                    break
                d.update(buf)
                target.write(buf)
        md5sum = d.hexdigest()

        # Rename the image file, use its md5sum as the new name
        image_file = os.path.join(CONF.images_dir, md5sum)
        os.rename(tmp_file, image_file)

        # Add additional image metadata
        image_md['checksum'] = md5sum
        image_md['location'] = 'file://%s' % image_file
        image_md['status'] = 'active'

        # Add the new image to the database
        image = self.db.images.add(**image_md)
        return utils.sanitize(image, IMAGES_INFO)

    def delete(self, image_id):
        """
        Delete an image
        """
        LOG.info('delete(image_id=%s)', image_id)

        # Get the image details
        image = self.db.images.show(id=image_id)

        # Delete the image in the database
        self.db.images.delete(id=image_id)

        # Delete the image file
        image_file = os.path.join(CONF.images_dir, image['checksum'])
        os.unlink(image_file)
