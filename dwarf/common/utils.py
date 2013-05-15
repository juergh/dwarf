#!/usr/bin/python

import random
import socket


def sanitize(obj, keys):

    def _sanitize(obj, keys):
        fields = {}
        for k in keys:
            if k in obj:
                fields[k] = obj[k]
            elif k == 'links':
                fields[k] = []
            else:
                fields[k] = None
        return fields

    if isinstance(obj, dict):
        return _sanitize(obj, keys)

    objs = []
    for o in obj:
        objs.append(_sanitize(o, keys))
    return objs


def show_request(req):
    print("---- BEGIN REQUEST HEADERS -----")
    for key in req.headers.keys():
        print('%s = %s' % (key, req.headers[key]))
    print("---- END REQUEST HEADERS -----")

#    if req.body:
#        print("---- BEGIN REQUEST BODY -----")
#        print('%s' % req.body)
#        print("---- END REQUEST BODY -----")


def get_local_ip():
    """
    Get the IP of the local machine
    """
    addr = '127.0.0.1'
    try:
        csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        csock.connect(('8.8.8.8', 80))
        (addr, _port) = csock.getsockname()
        csock.close()
    except socket.error:
        pass

    return addr


def generate_mac():
    """
    Generate a random MAC address
    """
    mac = [0x52, 0x54, 0x00,
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff),
           random.randint(0x00, 0xff)]
    return ':'.join(['%02x' % x for x in mac])


def get_ip(mac):
    """
    Get the IP associated with the given MAC address
    """
    addr = None
    leases = '/var/lib/libvirt/dnsmasq/default.leases'
    with open(leases, 'r') as fh:
        for line in fh.readlines():
            col = line.split()
            if col[1] == mac:
                addr = col[2]
                break

    return addr
