#!/usr/bin/python

from __future__ import print_function

from hashlib import md5
import os

from dwarf import db
from dwarf import exception
from dwarf.common import config

CONFIG = config.CONFIG


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self):
        """
        List all images
        """
        print('images.list()')
        return self.db.images.list()

    def show(self, image_id):
        print('images.show(image_id=%s)' % image_id)
        image = self.db.images.show(id=image_id)
        del image['deleted_at']
        return image

    def add(self, fh, md):
        print('images.add()')

        # Read the image data, store it in a temp location and calculate the
        # md5 sum
        tmp_file = '%s/tmp' % CONFIG.images_dir
        with open(tmp_file, 'wb') as target:
            d = md5()
            while True:
                buf = fh.read(4096)
                if not buf:
                    break
                d.update(buf)
                target.write(buf)
        md5sum = d.hexdigest()

        # Rename the image file, use its md5sum as the new name
        image_file = '%s/%s' % (CONFIG.images_dir, md5sum)
        os.rename(tmp_file, image_file)

        # Add additiional image metadata
        md['checksum'] = md5sum
        md['location'] = 'file://%s' % image_file
        md['status'] = 'active'

        # Update the database
        image = self.db.images.add(**md)

        # TODO: fix image properties
        image['properties'] = {}

        return image

    def delete(self, image_id):
        print('images.delete(image_id=%s)' % image_id)

        # Get the image details
        image = self.db.images.show(id=image_id)

        # Delete the image in the database
        self.db.images.delete(id=image_id)

        # Delete the image file
        image_file = '%s/%s' % (CONFIG.images_dir, image['checksum'])
        os.unlink(image_file)
