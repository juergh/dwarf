#!/usr/bin/python

from __future__ import print_function

from hashlib import md5
import os

from dwarf import db
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
        return self.db.images.show(id=image_id)

    def add(self, fh):
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

        # Update the database
        image = self.db.images.add(name=md5sum, size=1,
                                   status='active', is_public=1,
                                   location='file://%s' % image_file,
                                   checksum=md5sum, min_disk=0, min_ram=0,
                                   protected=0)

        # TODO: fix image properties
        image['properties'] = {}

        return image

    def delete(self, image_id):
        print('images.delete(image_id=%s)' % image_id)

        # Get the image details
        image = self.db.images.show(id=image_id)

        # Delete the image in the database
        # TODO: set status='deleted'
        self.db.images.delete(id=image_id)

        # Delete the image file
        image_file = '%s/%s' % (CONFIG.images_dir, image['checksum'])
        os.unlink(image_file)
