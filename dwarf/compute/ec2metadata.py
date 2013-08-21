#!/usr/bin/python

import bottle
import logging
import threading

from dwarf import db as dwarf_db
from dwarf import exception

from dwarf.common import config
from dwarf.common import utils

CONF = config.CONFIG
LOG = logging.getLogger(__name__)


def _ec2metadata_resources(server, keypair):
    """
    Return the supported metadata resources
    """
    resources = {
        'data': {
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
                'public-keys': '0=%s' % server['key_name'],
                'reservation-id': 'None',
                'security-groups': 'default'
            },
            'user-data': ''
        },
        'keys': {
            '0': {
                'openssh-key': keypair['public_key'],
            },
        },
    }

    return resources


def _ec2metadata_worker():
    """
    Ec2 metadata thread worker
    """
    LOG.info('Starting Ec2 metadata worker')

    # Cache to reduce database lookups
    servers = {}
    keypairs = {}

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

    db = dwarf_db.Controller()
    app = bottle.Bottle()

    @app.get('<url:re:[a-z0-9-/.]*>')
    @exception.catchall
    def http_get(url):   # pylint: disable=W0612
        """
        Ec2 metadata requests
        """
        # Client IP address
        ip = bottle.request.remote_addr

        if ip == '192.168.122.1' and ip not in servers:
            servers[ip] = {'id': 1, 'key_name': 'juergh'}
            keypairs[ip] = {'public_key': 'noneofyourbusiness!!'}

        # Query the database if the data for this client is not in the cache
        if ip not in servers:
            servers[ip] = db.servers.show(ip=ip)
            keypairs[ip] = db.keypairs.show(name=servers[ip]['key_name'])

        # Split the URL path into its individual components
        path = url.strip('/')
        components = path.split('/')

        # Check if the requested API version (first path component) is
        # supported
        version = components.pop(0)
        if version not in (versions + ['latest']):
            return ''.join('%s\n' % v for v in versions)

        # Get the client's metadata resources
        resources = _ec2metadata_resources(servers[ip], keypairs[ip])
        data = resources['data']
        keys = resources['keys']

        # Walk through the path components
        c_prev = ''
        for c in components:
            # Check if the client goes after the public keys
            if c_prev == 'public-keys' and c in keys:
                data = keys

            if c in data:
                data = data[c]
            else:
                bottle.abort(404)

            c_prev = c

        if isinstance(data, (str, unicode)):
            # Return the requested value
            return data

        elif isinstance(data, dict):
            # Return the directory listing
            return '\n'.join(sorted(data.iterkeys()))

        bottle.abort(404)

    host = CONF.ec2_metadata_host
    port = CONF.ec2_metadata_port
    LOG.info('Ec2 metadata server listening on %s:%s', host, port)
    bottle.run(app, host=host, port=port,
               handler_class=utils.BottleRequestHandler)


def thread():
    """
    Return the Ec2 metadata thread
    """
    return threading.Thread(target=_ec2metadata_worker)
