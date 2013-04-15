#!/usr/bin/python

from __future__ import print_function


class Controller(object):

    def __init__(self, args):
        self.args = args
#        self.db = db.Controller(args)
#        self.virt = virt.Controller(args)
#        self.metadata = metadata.Controller(args)

    def images(self, *_args, **_kwargs):
        print('compute.images()')
        return {'images': []}

    def image(self, *args, **_kwargs):
        print('compute.image(image_id=%s)' % args[0])
        return {'image': {'links': []}}

    def servers(self, *_args, **_kwargs):
        print('compute.servers()')
        return {'servers': []}
