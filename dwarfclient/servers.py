#!/usr/bin/python

import os
import shutil

from dwarfclient import db
from dwarfclient import exception
from dwarfclient import virt

from dwarfclient.common import config
from dwarfclient.common import log
from dwarfclient.common import utils

CONF = config.CONF
LOG = log.LOG


class Server(object):

    def __init__(self, details):
        self.id = 0
        self.memory = 1024 * 1024
        self.vcpus = 1
        self.add_details(details)
        self.domain = 'instance-d%07x' % self.id
        self.basepath = os.path.join(CONF.instances_dir, self.domain)

    def add_details(self, details):
        """
        Add details to the server object
        """
        for (k, v) in details.iteritems():
            setattr(self, k, v)


class Controller(object):

    def __init__(self, args):
        self.args = args
        self.db = db.Controller(args)
        self.virt = virt.Controller(args)

    def _init_server(self, name):
        details = self.db.init_server(name)
        return Server(details)

    def _get_server(self, sid):
        details = self.db.get_server(sid)
        server = Server(details)
        self._update_server(server)
        return server

    def _update_server(self, server):
        self.virt.update_server(server)

    def list(self):
        """
        Get a list of servers
        """
        servers = []
        for details in self.db.get_server_list():
            server = Server(details)
            self._update_server(server)
            servers.append(server)
        return servers

    def show(self, sid):
        """
        Get server details
        """
        return self._get_server(sid)

    def boot(self, name, image_file=''):
        """
        Boot a server
        """
        LOG.debug("server.boot: name='%s', image_file='%s'", name, image_file)

        if image_file is None:
            raise exception.ServerBootFailure(reason='No image specified')

        if not os.path.exists(image_file):
            raise exception.ServerBootFailure(reason="Image file '%s' does "
                                              "not exist" % image_file)
        # Create a new server
        server = self._init_server(name)

        # Create the base images
        base_images = utils.create_base_images(CONF.instances_base_dir,
                                               image_file)

        # Create the server base directory and the disk images
        os.makedirs(server.basepath)
        utils.create_local_images(server.basepath, base_images)

        # Finally boot the server
        self.virt.boot_server(server)
        return server

    def delete(self, sid):
        """
        Delete a server
        """
        server = self._get_server(sid)
        self.virt.delete_server(server)
        if os.path.exists(server.basepath):
            shutil.rmtree(server.basepath)
        self.db.delete_server(sid)

    def console_log(self, sid):
        """
        Return the server's console log
        """
        server = self._get_server(sid)
        path = '%s/console.log' % server.basepath
        utils.execute(['chown', os.getuid(), path], run_as_root=True)
        with open(path, 'r+') as fh:
            conlog = fh.read()
        return conlog

    def get_vnc_console(self, sid):
        """
        Get a VNC console to the server
        """
        server = self._get_server(sid)
        return getattr(server, 'vnc_display')

    def reboot(self, sid):
        """
        Reboot a server
        """
        server = self._get_server(sid)
        self.virt.reboot_server(server)
        return server
