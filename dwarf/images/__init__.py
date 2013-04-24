#!/usr/bin/python

from __future__ import print_function


class Controller(object):

    def __init__(self):
        pass
#        self.db = db.Controller(args)

    def index(self, *_args, **_kwargs):
        print('images.index()')
        return {'images': []}

    def show(self, *_args, **_kwargs):
        print('images.show()')
#        image_id = args[0]
        return {'image': {}}
