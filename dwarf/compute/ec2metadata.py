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

import bottle
import logging

from dwarf import api_server
from dwarf import config
from dwarf import db
from dwarf import exception

CONF = config.Config()
LOG = logging.getLogger(__name__)

DB = db.Controller()


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
            'ami-id': 'ami-00000000',
            'ami-launch-index': '0',
            'ami-manifest-path': 'FIXME',
            'block-device-mapping': {
                'ami': 'vda',
                'root': '/dev/vda',
                'ephemeral0': '/dev/vdb',
            },
            'hostname': server['name'],
            'instance-action': 'None',
            'instance-id': 'i-%08x' % int(server['int_id']),
            'instance-type': 'dwarf.small',
            'local-hostname': server['name'],
            'local-ipv4': 'None',
            'placement': {
                'availability-zone': 'dwarf',
            },
            'public-hostname': '',
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


@exception.catchall
def _route_ec2(url):
    """
    Route:  <url:re:[a-z0-9-/.]*>
    Method: GET
    """
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

    # Client IP address
    ip = bottle.request.remote_addr

    # Database lookup
    server = DB.servers.show(ip=ip)
    keypair = DB.keypairs.show(name=server['key_name'])

    # Split the URL path into its individual components
    path = url.strip('/')
    components = path.split('/')

    # Check if the requested API version (first path component) is supported
    version = components.pop(0)
    if version not in versions + ['latest']:
        return _ec2metadata_format(versions)

    # Get the client's metadata resources
    data = _ec2metadata_resources(server, keypair)

    # Walk through the path components
    for c in components:
        # Bail out if accessing hidden or non-existing keys
        if c == '_key_name' or c not in data:
            bottle.abort(404)
        else:
            data = data[c]

    # Format and return the data
    return _ec2metadata_format(data)


class Ec2MetadataServer(api_server.ApiServer):
    def __init__(self):
        super(Ec2MetadataServer, self).__init__('Ec2 metadata',
                                                CONF.libvirt_bridge_ip,
                                                CONF.ec2_metadata_port)

        self.app.route('<url:re:[a-z0-9-/.]*>',
                       method='GET',
                       callback=_route_ec2)
