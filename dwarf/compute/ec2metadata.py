#!/usr/bin/python

import bottle
import logging
import threading

from wsgiref.simple_server import WSGIRequestHandler

from dwarf import exception

from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG
LOG = logging.getLogger(__name__)

_EC2_METADATA_THREAD = None


class Ec2MetadataRequestHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        LOG.info(fmt, *args)


class Ec2MetadataThread(threading.Thread):
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.server = {}

        global _EC2_METADATA_THREAD   # pylint: disable=W0603
        _EC2_METADATA_THREAD = self

    def _resources(self, server):
        """
        Return the supported metadata resources
        """
        resources = {
            'meta-data': {
                'ami-id': 'ami-%08x' % int(server['id']),
                'ami-launch-index': '0',
                'ami-manifest-path': 'FIXME',
                'block-device-mapping': {
                    'ami': 'vda',
                    'root': '/dev/vda',
                    'ephemeral0': '/dev/vdb',
                },
                'hostname': 'TBD',
                'instance-action': 'None',
                'instance-id': 'TBD',
                'instance-type': 'dwarf.small',
                'local-hostname': 'TBD',
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

        return resources

    def add_server(self, server):
        """
        Add a (compute) server to the metadata server
        """
        LOG.info('add_server(server=%s', server)

        if server['ip'] in self.server:
            LOG.warning('server with IP %s exists already', server['ip'])
            return

        # Add the server resources
        self.server[server['ip']] = self._resources(server)

        # Add the IP route
        utils.execute(['iptables',
                       '-t', 'nat',
                       '-A', 'PREROUTING',
#                       '-s', '0.0.0.0/0',
                       '-s', server['ip'],
                       '-d', '169.254.169.254/32',
                       '-p', 'tcp',
                       '-m', 'tcp',
                       '--dport', 80,
                       '-j', 'REDIRECT',
                       '--to-port', self.port],
                      run_as_root=True)

    def delete_server(self, server):
        """
        Delete a (compute) server from the metadata server
        """
        LOG.info('delete_server(server=%s', server)

        # Delete the IP route
        utils.execute(['iptables',
                       '-t', 'nat',
                       '-D', 'PREROUTING',
#                       '-s', '0.0.0.0/0',
                       '-s', server['ip'],
                       '-d', '169.254.169.254/32',
                       '-p', 'tcp',
                       '-m', 'tcp',
                       '--dport', 80,
                       '-j', 'REDIRECT',
                       '--to-port', self.port],
                      run_as_root=True,
                      check_exit_code=False)

        if server['ip'] not in self.server:
            LOG.warning('server with IP %s does not exist', server['ip'])
            return

        # Delete the server resources
        del self.server[server['ip']]

    def run(self):   # pylint: disable=R0912
        LOG.info('Starting Ec2 metadata thread')

        # Supported API versions
        versions = ['1.0',
                    '2007-01-19',
                    '2007-03-01',
                    '2007-08-29',
                    '2007-10-10',
                    '2007-12-15',
                    '2008-02-01',
                    '2008-09-01',
                    '2009-04-04']

        app = bottle.Bottle()

        @app.get('<url:re:[a-z0-9-/.]*>')
        @exception.catchall
        def http_get(url):   # pylint: disable=W0612
            """
            Ec2 metadata requests
            """
            client_ip = bottle.request.remote_addr

            # Check if we know about this client
            if client_ip not in self.server:
                bottle.abort(404)

            path = url.strip('/')
            components = path.split('/')

            # Check if the requested API version is supported
            version = components.pop(0)
            if version not in (versions + ['latest']):
                return ''.join('%s\n' % v for v in versions)

            # Walk through the path components
            data = self.server[client_ip]
            for c in components:
                if c in data:
                    data = data[c]
                else:
                    bottle.abort(404)

            if isinstance(data, (str, unicode)):
                # Return the requested value
                return data

            elif isinstance(data, dict):
                # Return the directory listing
                return '\n'.join(sorted(data.iterkeys()))

            bottle.abort(404)

        bottle.run(app, host='192.168.122.1', port=self.port,
#        bottle.run(app, host='192.168.1.37', port=self.port,
                   handler_class=Ec2MetadataRequestHandler)


class Controller(object):

    def add_server(self, server):
        # Add the compute server data
        _EC2_METADATA_THREAD.add_server(server)

    def delete_server(self, server):
        # Delete the compute server data
        _EC2_METADATA_THREAD.delete_server(server)
