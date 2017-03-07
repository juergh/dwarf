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

from copy import deepcopy

from tests import data
from tests import utils

from dwarf import exception

FLAVOR = """{
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "disk": "{{disk}}",
    "id": "{{id}}",
    "int_id": "{{int_id}}",
    "name": "{{name}}",
    "ram": "{{ram}}",
    "updated_at": "{{updated_at}}",
    "vcpus": "{{vcpus}}"
}"""


def show_flavor_resp(flavor, **kwargs):
    return utils.json_render(FLAVOR, flavor, **kwargs)


def list_flavors_resp(flavors):
    return [utils.json_render(FLAVOR, f) for f in flavors]


SERVER = """{
    "config_drive": "{{config_drive}}",
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "flavor_id": "{{flavor_id}}",
    "id": "{{id}}",
    "image_id": "{{image_id}}",
    "int_id": "{{int_id}}",
    "ip": "{{ip}}",
    "key_name": "{{key_name}}",
    "mac_address": "{{mac_address}}",
    "name": "{{name}}",
    "status": "{{status}}",
    "updated_at": "{{updated_at}}"
}"""


def create_server_resp(server):
    return utils.json_render(SERVER, server)


def show_server_resp(server):
    return utils.json_render(SERVER, server)


KEYPAIR = """{
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "id": "{{id}}",
    "int_id": "{{int_id}}",
    "fingerprint": "{{fingerprint}}",
    "name": "{{name}}",
    "public_key": "{{public_key}}",
    "updated_at": "{{updated_at}}"
}"""


def create_keypair_resp(keypair):
    return utils.json_render(KEYPAIR, keypair)


IMAGE = """{
    "checksum": "{{checksum}}",
    "container_format": "{{container_format}}",
    "created_at": "{{created_at}}",
    "deleted": "{{deleted}}",
    "deleted_at": "{{deleted_at}}",
    "disk_format": "{{disk_format}}",
    "file": "{{file}}",
    "id": "{{id}}",
    "int_id": "{{int_id}}",
    "is_public": "{{is_public}}",
    "min_disk": "{{min_disk}}",
    "min_ram": "{{min_ram}}",
    "name": "{{name}}",
    "owner": "{{owner}}",
    "protected": "{{protected}}",
    "size": "{{size}}",
    "status": "{{status}}",
    "updated_at": "{{updated_at}}"
}"""


def create_image_resp(image):
    return utils.json_render(IMAGE, image)


flavor1 = data.flavor['100']
flavor2 = data.flavor['101']
flavor3 = data.flavor['102']

server1 = data.server['11111111-2222-3333-4444-555555555555']

keypair1 = data.keypair['11111111-2222-3333-4444-555555555555']

image1 = data.image['11111111-2222-3333-4444-555555555555']


class DbTestCase(utils.TestCase):

    def setUp(self):
        super(DbTestCase, self).setUp()

    def tearDown(self):
        super(DbTestCase, self).tearDown()

    def test_init_db(self):
        self.assertEqual(self.db.servers.list(), [])
        self.assertEqual(self.db.keypairs.list(), [])
        self.assertEqual(self.db.images.list(), [])
        self.assertEqual(self.db.flavors.list(),
                         list_flavors_resp([flavor1, flavor2, flavor3]))

    def test_dump_db(self):
        self.db.dump()
        self.db.dump(table='flavors')

    # -------------------------------------------------------------------------
    # Flavor

    def test_show_flavor(self):
        resp = self.db.flavors.show(id=flavor1['id'])
        self.assertEqual(resp, show_flavor_resp(flavor1))

        resp = self.db.flavors.show(name=flavor1['name'])
        self.assertEqual(resp, show_flavor_resp(flavor1))

    def test_delete_flavor_by_id(self):
        self.db.flavors.delete(id=flavor1['id'])
        resp = self.db.flavors.list()
        self.assertEqual(resp, list_flavors_resp([flavor2, flavor3]))

    def test_delete_flavor_by_name(self):
        self.db.flavors.delete(name=flavor1['name'])
        resp = self.db.flavors.list()
        self.assertEqual(resp, list_flavors_resp([flavor2, flavor3]))

    def test_delete_flavor_not_found(self):
        self.assertRaises(exception.NotFound, self.db.flavors.delete,
                          id='no_such_id')

    def test_create_flavor_conflict(self):
        self.assertRaises(exception.Conflict, self.db.flavors.create,
                          id=flavor1['id'])

    def test_update_flavor(self):
        resp = self.db.flavors.update(id=flavor1['id'], name='new name',
                                      disk='new disk', foo='bar')
        self.assertEqual(resp, show_flavor_resp(flavor1, name='new name',
                                                disk='new disk'))

    # -------------------------------------------------------------------------
    # Server

    def test_create_server(self):
        resp = self.db.servers.create(**server1)
        self.assertEqual(resp, create_server_resp(server1))

        resp = self.db.servers.show(name=server1['name'])
        self.assertEqual(resp, show_server_resp(server1))

        resp = self.db.servers.show(ip=server1['ip'])
        self.assertEqual(resp, show_server_resp(server1))

    # -------------------------------------------------------------------------
    # Keypair

    def test_create_keypair(self):
        resp = self.db.keypairs.create(**keypair1)
        self.assertEqual(resp, create_keypair_resp(keypair1))

    # -------------------------------------------------------------------------
    # Image

    def test_create_image(self):
        resp = self.db.images.create(**image1)
        self.assertEqual(resp, create_image_resp(image1))

    def test_delete_protected_image(self):
        protected = deepcopy(image1)
        protected['protected'] = 'True'
        self.db.images.create(**protected)
        self.assertRaises(exception.Forbidden, self.db.images.delete,
                          id=protected['id'])

    # -------------------------------------------------------------------------
    # Code coverage

    def test_init_cc(self):
        self.db.init()

    def test_delete_cc(self):
        self.db.delete()

    def test_dump_cc(self):
        self.db.dump(table='no_such_table')

    def test_show_cc(self):
        self.assertRaises(exception.NotFound, self.db.images.show,
                          id='no_such_id')
