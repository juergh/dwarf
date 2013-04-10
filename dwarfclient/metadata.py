#!/usr/bin/python

import os
import signal
import socket
import sys
import time

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from dwarfclient import exception
from dwarfclient.common import config
from dwarfclient.common import log
from dwarfclient.common import utils

CONF = config.CONF
LOG = log.LOG


class MetadataRequestHandler(BaseHTTPRequestHandler):

    def _send_reply(self, response):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(response)

    def log_message(self, fmt, *args):
        LOG.debug('%s - %s', self.address_string(), fmt % args)

    def do_GET(self):
        path = self.path.strip('/')
        components = path.split('/')

        # check if the requested API version is supported
        version = components.pop(0)
        if version not in (self.server.versions + ['latest']):
            self._send_reply(''.join('%s\n' % v for v in self.server.versions))
            return

        # Walk through the path components
        data = self.server.data
        for c in components:
            if c in data:
                data = data[c]
            else:
                self.send_error(404)
                return

        if isinstance(data, (str, unicode)):
            # Return the requested value
            reply = data

        elif isinstance(data, dict):
            # Return the directory listing, append a '/' to subdirectories
            reply = ''
            for key in sorted(data.iterkeys()):
                reply += key
                if isinstance(data[key], dict):
                    reply += '/'
                reply += '\n'

        self._send_reply(reply)


class MetadataServer(HTTPServer):

    def __init__(self, port, server):

        # Supported API versions
        self.versions = ['1.0',
                         '2007-01-19',
                         '2007-03-01',
                         '2007-08-29',
                         '2007-10-10',
                         '2007-12-15',
                         '2008-02-01',
                         '2008-09-01',
                         '2009-04-04']

        # Construct the metadata
        self.data = {
            'meta-data': {
                'ami-id': 'ami-%08x' % server.id,
                'ami-launch-index': '0',
                'ami-manifest-path': 'FIXME',
                'block-device-mapping': {
                    'ami': 'vda',
                    'root': '/dev/vda',
                    'ephemeral0': '/dev/vdb',
                },
                'hostname': server.name,
                'instance-action': 'None',
                'instance-id': server.domain,
                'instance-type': 'dwarf.small',
                'local-hostname': server.name,
                'local-ipv4': 'None',
                'placement': {
                    'availability-zone': 'nova',
                },
                'public-hostname': 'dwarf-host',
                'reservation-id': 'None',
                'security-groups': 'default'
            },
            'user-data': ''
        }

        HTTPServer.__init__(self, ('', port), MetadataRequestHandler)


class Controller(object):

    def __init__(self, args):
        self.args = args

    def _write_pid_file(self, server, pid, port):
        path = '%s/%s.pid' % (CONF.run_dir, server.domain)
        with open(path, 'w') as fh:
            fh.write('%s %s' % (pid, port))

    def _read_pid_file(self, server):
        path = '%s/%s.pid' % (CONF.run_dir, server.domain)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as fh:
            data = fh.read()
        return [int(x) for x in data.split()]

    def _remove_pid_file(self, server):
        path = '%s/%s.pid' % (CONF.run_dir, server.domain)
        if os.path.exists(path):
            os.remove(path)

    def start(self, server):
        """
        Fork a metadata server
        """
        # Do the UNIX double-fork magic
        try:
            pid = os.fork()
            if pid > 0:
                return
        except OSError as e:
            raise exception.MetadataStartFailure(reason='fork #1 failed (%s)' %
                                                 e.strerror)

        # Decouple from the parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)

        # Do the second fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError as e:
            raise exception.MetadataStartFailure(reason='fork #2 failed (%s)' %
                                                 e.strerror)

        # Find an unused port for the HTTP server
        port = 9000
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                sock.bind(('', port))
                break
            except socket.error as e:
                port += 1
        sock.close()

        # Save the PID (and the port) of the HTTP server so we can kill it
        # later
        self._write_pid_file(server, os.getpid(), port)

        # Create the HTTP server but don't start it until the VM gets an IP and
        # the iptables rule is added
        meta = MetadataServer(port, server)

        addr = None
        while addr is None:
            time.sleep(5)
            addr = utils.find_ip(server.mac_address)

        utils.execute(['iptables',
                       '-t', 'nat',
                       '-A', 'PREROUTING',
                       '-s', addr,
                       '-d', '169.254.169.254/32',
                       '-p', 'tcp',
                       '-m', 'tcp',
                       '--dport', 80,
                       '-j', 'REDIRECT',
                       '--to-port', port],
                      run_as_root=True)

        meta.serve_forever()

    def stop(self, server):
        """
        Terminate a metadata server
        """
        # Get the PID and port of the HTTP server
        (pid, port) = self._read_pid_file(server)

        # Delete the iptables rule
        utils.execute(['iptables',
                       '-t', 'nat',
                       '-D', 'PREROUTING',
                       '-s', server.ip_address,
                       '-d', '169.254.169.254/32',
                       '-p', 'tcp',
                       '-m', 'tcp',
                       '--dport', 80,
                       '-j', 'REDIRECT',
                       '--to-port', port],
                      run_as_root=True)

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        self._remove_pid_file(server)

    def update_server(self, server):
        """
        Update a server object with information about its metadata server
        """
        (pid, port) = self._read_pid_file(server)
        # Check if the metadata server is running
        try:
            os.kill(pid, 0)
            server.add_details({'metadata_server_pid': pid,
                                'metadata_server_port': port})
        except OSError:
            pass
