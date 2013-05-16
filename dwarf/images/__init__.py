#!/usr/bin/python

from __future__ import print_function

from hashlib import md5
import os

from dwarf import db
from dwarf import exception

from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG

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
        print('images.list()')

        _images = self.db.images.list()
        return utils.sanitize(_images, IMAGES_INFO)

    def show(self, image_id):
        print('images.show(image_id=%s)' % image_id)

        _image = self.db.images.show(id=image_id)
        return utils.sanitize(_image, IMAGES_INFO)

    def add(self, image_fh, image_md):
        print('images.add()')

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
        image_file = '%s/%s' % (CONF.images_dir, md5sum)
        os.rename(tmp_file, image_file)

        # Add additional image metadata
        image_md['checksum'] = md5sum
        image_md['location'] = 'file://%s' % image_file
        image_md['status'] = 'active'

        # Add the new image to the database
        _image = self.db.images.add(**image_md)
        return utils.sanitize(_image, IMAGES_INFO)

    def delete(self, image_id):
        print('images.delete(image_id=%s)' % image_id)

        # Get the image details
        _image = self.db.images.show(id=image_id)

        # Delete the image in the database
        self.db.images.delete(id=image_id)

        # Delete the image file
        image_file = '%s/%s' % (CONF.images_dir, _image['checksum'])
        os.unlink(image_file)
