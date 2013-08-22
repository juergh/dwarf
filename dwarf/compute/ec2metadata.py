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


def _ec2metadata_format(data):
    """
    Format Ec2 metadata
    """
    # Handle dicts
    if isinstance(data, dict):
        output = ''
        for (key, val) in data.iteritems():
            # Skip hidden keys
            if key == '_key_name':
                continue

            output += key
            if isinstance(val, dict):
                # Handle hidden keys
                if '_key_name' in val:
                    output += '=' + str(val['_key_name'])
                else:
                    output += '/'
            output += '\n'

        # Drop the trailing '\n'
        return output[:-1]

    # Handle lists
    elif isinstance(data, list):
        return '\n'.join(data)

    # Handle everything else
    else:
        return str(data)


def _ec2metadata_resources(server, keypair):
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
            'public-keys': {
                '0': {
                    '_key_name': server['key_name'],
                    'openssh-key': keypair['public_key'],
                },
            },
            'reservation-id': 'None',
            'security-groups': 'default'
        },
        'user-data': ''
    }

    return resources


def _ec2metadata_worker():
    """
    Ec2 metadata thread worker
    """
    LOG.info('Starting Ec2 metadata worker')

    # Cache to minimize database lookups
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

        # Query the database if the server and keypair data of this client is
        # not in the cache
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
            return _ec2metadata_format(versions)

        # Get the client's metadata resources
        data = _ec2metadata_resources(servers[ip], keypairs[ip])

        # Walk through the path components
        for c in components:
            # Bail out if accessing hidden or non-existing keys
            if c == '_key_name' or c not in data:
                bottle.abort(404)
            else:
                data = data[c]

        # Format and return the data
        return _ec2metadata_format(data)

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