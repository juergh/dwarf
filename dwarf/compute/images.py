#!/usr/bin/python

from __future__ import print_function

from dwarf import db


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self):
        """
        List all images
        """
        print('compute.images.list()')
        images = self.db.images.list()
        return images

    def show(self, image_id):
        """
        Show image details
        """
        print('compute.images.show()')
        image = self.db.images.show(id=image_id)

        for key in ('deleted', 'deleted_at'):
            del image[key]
        image['links'] = []

        return image
