#!/usr/bin/env python
#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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
# limitations under the License.    'properties': {},

now = '2001-02-03 04:05:06'
uuid = '11111111-2222-3333-4444-555555555555'

image = {
    '11111111-2222-3333-4444-555555555555': {
        'checksum': 'd6ac46d3ba444c0a3226339a5c04111e',   # md5sum of 'data'
        'container_format': 'bare',
        'created_at': now,
        'data': 'Test image 1 data',
        'data_chunked': '4\r\nTest\r\n9\r\n image 1 \r\n4\r\ndata\r\n0\r\n',
        'deleted': 'False',
        'deleted_at': '',
        'disk_format': 'raw',
        'file': '/tmp/dwarf/images/11111111-2222-3333-4444-555555555555',
        'id': '11111111-2222-3333-4444-555555555555',
        'int_id': '1',
        'min_disk': '',
        'min_ram': '',
        'name': 'Test image 1',
        'owner': '',
        'properties': {},
        'protected': 'False',
        'size': '17',
        'status': 'active',
        'updated_at': now,
        'visibility': 'private'
    },
    '22222222-3333-4444-5555-666666666666': {
        'checksum': 'b23afbb294b9b9b303b1af1fb5354b8e',   # md5sum of 'data'
        'container_format': 'bare',
        'created_at': now,
        'data': 'Test image 2 data',
        'data_chunked': '4\r\nTest\r\n9\r\n image 2 \r\n4\r\ndata\r\n0\r\n',
        'deleted': 'False',
        'deleted_at': '',
        'disk_format': 'raw',
        'file': '/tmp/dwarf/images/22222222-3333-4444-5555-666666666666',
        'id': '22222222-3333-4444-5555-666666666666',
        'int_id': '2',
        'min_disk': '',
        'min_ram': '',
        'name': 'Test image 2',
        'owner': '',
        'properties': {},
        'protected': 'False',
        'size': '17',
        'status': 'active',
        'updated_at': now,
        'visibility': 'private'
    },
}

flavor = {
    '100': {
        'created_at': now,
        'deleted': 'False',
        'deleted_at': '',
        'disk': '10',
        'id': '100',
        'int_id': '1',
        'name': 'standard.xsmall',
        'ram': '512',
        'updated_at': now,
        'vcpus': '1',
    },
    '101': {
        'created_at': now,
        'deleted': 'False',
        'deleted_at': '',
        'disk': '30',
        'id': '101',
        'int_id': '2',
        'name': 'standard.small',
        'ram': '768',
        'updated_at': now,
        'vcpus': '1',
    },
    '102': {
        'created_at': now,
        'deleted': 'False',
        'deleted_at': '',
        'disk': '30',
        'id': '102',
        'int_id': '3',
        'name': 'standard.medium',
        'ram': '1024',
        'updated_at': now,
        'vcpus': '1',
    },
}

keypair = {
    '11111111-2222-3333-4444-555555555555': {
        'created_at': now,
        'deleted': 'False',
        'deleted_at': '',
        'id': '11111111-2222-3333-4444-555555555555',
        'int_id': '1',
        'fingerprint': 'ea:3a:a1:40:49:63:c3:50:96:b6:a3:d9:d8:57:78:1c',
        'name': 'Test keypair 1',
        'public_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC3BdGcpV0k4FgcVTR'
                      'ldq5WQlJ1pg/Vo4bNiWSwCmeeDXsABEw2b5vDgHm1Rq3AgRni3ec+Ba'
                      'ckw4ESjzZhV16GQPWrGsxiAuefom5A+uDq6t8Zc9lpH9XJfNX9sIu5p'
                      '3P/Ic3H7AfxU7wnH66cZmQAUPt9vr7mqsr8AU+sgetfGlfxmk5ogWFG'
                      'eKMhQdzM+eA8VYsyH9Co4K1DNS6eyWKawA2G6C1p2uY3DImFlx651eD'
                      '3Ie4fqoGX7uj13ZRSHDCxeVI1lUeWraIKASTgvCQmrDebYPniD0LFa0'
                      '9lIrzQ95TTUDOk2XcQ292Bm1M7YRWY8OAum5bhj+JkSLxFNnDf',
        'updated_at': now,
    },
    '22222222-3333-4444-5555-666666666666': {
        'created_at': now,
        'deleted': 'False',
        'deleted_at': '',
        'id': '22222222-3333-4444-5555-666666666666',
        'int_id': '2',
        'fingerprint': 'f1:82:dc:af:6a:85:06:71:74:c4:25:4f:aa:88:2c:e3',
        'name': 'Test keypair 2',
        'public_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDFQBq363pwh80sA3o'
                      '7FqkCbr1ZC/e+HtNUYycUaSypgmudH6dq0nx0U07DLSijYIH0d+DEsl'
                      'yx+r5DLJ+wssQzSS6p/NAKGWzUn6jE3w2mKKCalH1iqz9v7RCZeREVv'
                      'Xc55lDbIwcb9H1fHn17OgmsWZZ9ApppzQBdczMHsr9GQ/dsbGPewweA'
                      'WxM4Lt/tm7MFxFU9m+KyDStSfEf2QmiApFbjTFZYLARQePCYmbrD8hX'
                      'f0ZPD6HJCe4MyUgYQBwAAnZ4sq2fSV/U6kqhmhnv9WnUD/ianGuFNgp'
                      'CjkNTepm8ny6+H+i/YKp4h1jAEc/bi+xPksN5tJAVuXI1b6iy7',
        'updated_at': now,
    },
}


server = {
    '11111111-2222-3333-4444-555555555555': {
        'config_drive': 'False',
        'created_at': now,
        'deleted': 'False',
        'deleted_at': '',
        'flavor_id': '100',
        'id': '{{id}}',
        'image_id': '11111111-2222-3333-4444-555555555555',
        'int_id': '1',
        'ip': '10.10.10.1',
        'key_name': 'Test keypair 1',
        'mac_address': '',
        'name': 'Test server 1',
        'status': 'active',
        'updated_at': now,
    },
}
