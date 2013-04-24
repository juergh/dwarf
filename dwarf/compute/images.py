#!/usr/bin/python

from __future__ import print_function

from dwarf import db


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self, *_args, **_kwargs):
        """
        List all images
        """
        print('compute.images.list()')
        return {'images': []}

    def show(self, *_args, **_kwargs):
        """
        Show image details
        """
        print('compute.images.show()')
        #image_id = args[0]
        return {'image': {'links': []}}
