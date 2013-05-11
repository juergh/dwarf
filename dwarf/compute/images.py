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
        return []

    def show(self, _image_id):
        """
        Show image details
        """
        print('compute.images.show()')
        return {'links': []}
