#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

import logging

from dwarf import db

from dwarf import utils

LOG = logging.getLogger(__name__)

IMAGES_INFO = ('id', 'links', 'name')
IMAGES_DETAIL = ('created_at', 'id', 'is_public', 'links', 'name', 'size',
                 'status', 'updated_at', 'location')


class Controller(object):

    def __init__(self):
        self.db = db.Controller()

    def list(self, detail=True):
        """
        List all images
        """
        LOG.info('list(detail=%s)', detail)

        images = self.db.images.list()
        if detail:
            return utils.sanitize(images, IMAGES_DETAIL)
        else:
            return utils.sanitize(images, IMAGES_INFO)

    def show(self, image_id):
        """
        Show image details
        """
        LOG.info('show(image_id=%s)', image_id)

        image = self.db.images.show(id=image_id)
        return utils.sanitize(image, IMAGES_DETAIL)
