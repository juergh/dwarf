#!/usr/bin/env python
#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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
import os
import sqlite3 as sq3
import uuid

from time import gmtime, strftime

from dwarf import exception
from dwarf import config

CONF = config.Config()
LOG = logging.getLogger(__name__)

_DB_COLS = ['created_at', 'updated_at', 'deleted_at', 'deleted', 'id',
            'int_id']

DB_SERVERS_COLS = _DB_COLS + ['name', 'status', 'image_id', 'flavor_id',
                              'key_name', 'mac_address', 'ip', 'config_drive']
DB_KEYPAIRS_COLS = _DB_COLS + ['name', 'fingerprint', 'public_key']
DB_IMAGES_COLS = _DB_COLS + ['name', 'disk_format', 'container_format', 'size',
                             'status', 'file', 'checksum', 'min_disk',
                             'min_ram', 'owner', 'protected', 'visibility']
DB_FLAVORS_COLS = _DB_COLS + ['name', 'disk', 'ram', 'vcpus']

TRUE = 'True'
FALSE = 'False'


def _print_rows(objs):
    result = []
    for obj in objs:
        result.append(' | '.join(str(o) for o in obj))
    print('\n'.join(result) + '\n')


def _get_from_dict(keys, **kwargs):
    """
    Find key in dict and return (key, val) pair
    """
    for key in keys:
        val = kwargs.get(key, None)
        if val:
            return (key, val)


def _now():
    return strftime('%Y-%m-%d %H:%M:%S', gmtime())


def _to_string_bool(obj):
    if isinstance(obj, bool):
        if obj:
            return TRUE
    elif obj.lower() in ['1', 'yes', 'true', 'on']:
        return TRUE
    return FALSE


class Table(object):

    def __init__(self, db, table, cols, is_unique=None, is_bool=None):
        self.db = db
        self.table = table
        self.cols = cols
        self.is_unique = is_unique
        if is_bool is None:
            self.is_bool = []
        else:
            self.is_bool = is_bool

    def init(self):
        """
        Initialize (create) the table
        """
        LOG.info('%s : init()', self.table)

        # Convert the cols array to an sqlite formatting string, i.e.,:
        # 'id TEXT, name TEXT, status TEXT, key TEXT'
        fmt = ','.join(['%s TEXT' % c for c in self.cols])

        con = sq3.connect(self.db)
        with con:
            cur = con.cursor()
            cur.execute('CREATE TABLE %s (%s)' % (self.table, fmt))

    def dump(self):
        """
        Return all table rows
        """
        LOG.info('%s : dump()', self.table)

        con = sq3.connect(self.db)
        with con:
            cur = con.cursor()
            cur.execute('SELECT * FROM %s' % self.table)
            rows = cur.fetchall()

        return rows

    def create(self, **kwargs):
        """
        Create a new table row
        """
        LOG.info('%s : create(%s)', self.table, kwargs)

        con = sq3.connect(self.db)
        with con:
            cur = con.cursor()

            # Check if the row already exists
            if self.is_unique:
                key = self.is_unique
                val = kwargs.get(key, None)
                if val:
                    cur.execute('SELECT * FROM %s WHERE %s=? AND deleted=?' %
                                (self.table, key), (val, FALSE))
                    if cur.fetchone():
                        raise exception.Conflict(reason='%s %s already '
                                                 'exists' %
                                                 (self.table.rstrip('s'), val))

            # Create a new (UU)ID if necessary
            if 'id' not in kwargs:
                kwargs['id'] = str(uuid.uuid4())

            # Autoincrement the integer ID
            rid = 1
            cur.execute('SELECT max(cast(int_id as INT)) FROM %s' % self.table)
            row = cur.fetchone()
            if row[0] is not None:
                rid = int(row[0]) + 1
            kwargs['int_id'] = rid

            # Fill in the missing row properties
            now = _now()
            kwargs['created_at'] = now
            kwargs['updated_at'] = now
            kwargs['deleted'] = FALSE

            # Create the array of table row values (in the right column order)
            vals = []
            for c in self.cols:
                if c in self.is_bool:
                    val = _to_string_bool(kwargs.get(c, FALSE))
                else:
                    val = kwargs.get(c, '')
                vals.append(val)

            # Create the sqlite formatting string, i.e., '?,?,?,?'
            fmt = ('?,' * len(self.cols)).rstrip(',')

            # Insert the new row
            cur.execute('INSERT into %s values (%s)' % (self.table, fmt), vals)

        return self.show(id=kwargs['id'])

    def update(self, **kwargs):
        """
        Update a table row
        """
        LOG.info('%s : update(%s)', self.table, kwargs)

        con = sq3.connect(self.db)
        with con:
            cur = con.cursor()

            # Fill in the missing row properties
            now = _now()
            kwargs['updated_at'] = now

            # Create the sqlite formatting string and values
            fmt = ''
            vals = []
            for c in self.cols:
                if c in kwargs:
                    fmt = '%s,%s=?' % (fmt, c)
                    if c in self.is_bool:
                        val = _to_string_bool(kwargs[c])
                    else:
                        val = kwargs[c]
                    vals.append(val)
            fmt = fmt.lstrip(',')
            vals.append(kwargs['id'])

            # Update the row
            cur.execute('UPDATE %s SET %s WHERE id=?' % (self.table, fmt),
                        vals)

        return self.show(id=kwargs['id'])

    def delete(self, **kwargs):
        """
        Delete a table row
        """
        LOG.info('%s : delete(%s)', self.table, kwargs)
        (key, val) = _get_from_dict(['id', 'name'], **kwargs)

        con = sq3.connect(self.db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM %s WHERE %s=? AND deleted=?' %
                        (self.table, key), (val, FALSE))
            sq3_row = cur.fetchone()

            # Check if the row exists
            if not sq3_row:
                raise exception.NotFound(reason='%s %s not found' %
                                         (self.table.rstrip('s'), val))

            # Check if the row is protected
            protected = dict(zip(sq3_row.keys(), sq3_row)).get('protected',
                                                               'false').lower()
            if protected == 'true':
                raise exception.Forbidden(reason='%s %s is protected' %
                                          (self.table.rstrip('s'), val))

            # Delete the row
            now = _now()
            cur.execute('UPDATE %s SET deleted_at=?, updated_at=?, deleted=?'
                        'WHERE %s=?' % (self.table, key),
                        (now, now, TRUE, val))

    def list(self):
        """
        Get all table rows, converted to an array of dicts
        """
        LOG.info('%s : list()', self.table)

        con = sq3.connect(self.db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM %s WHERE deleted=?' % self.table,
                        (FALSE, ))
            sq3_rows = cur.fetchall()

        # Convert to an array of dicts
        rows = []
        for row in sq3_rows:
            rows.append(dict(zip(row.keys(), row)))

        LOG.debug('%s : %s', self.table, rows)
        return rows

    def show(self, **kwargs):
        """
        Get a single table row, converted to a dict
        """
        LOG.info('%s : show(%s)', self.table, kwargs)
        (key, val) = _get_from_dict(['id', 'name', 'ip'], **kwargs)

        con = sq3.connect(self.db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM %s WHERE %s=? AND deleted=?' %
                        (self.table, key), (val, FALSE))
            sq3_row = cur.fetchone()

        if not sq3_row:
            raise exception.NotFound(reason='%s %s not found' %
                                     (self.table.rstrip('s'), val))

        # Convert to a dict
        row = dict(zip(sq3_row.keys(), sq3_row))

        LOG.debug('%s : %s', self.table, row)
        return row


class Controller(object):

    def __init__(self):
        self.servers = Table(CONF.dwarf_db, 'servers', DB_SERVERS_COLS,
                             is_unique='name',
                             is_bool=('config_drive', 'deleted'))
        self.keypairs = Table(CONF.dwarf_db, 'keypairs', DB_KEYPAIRS_COLS,
                              is_unique='name',
                              is_bool=('deleted', ))
        self.images = Table(CONF.dwarf_db, 'images', DB_IMAGES_COLS,
                            is_unique='id',
                            is_bool=('deleted', 'protected'))
        self.flavors = Table(CONF.dwarf_db, 'flavors', DB_FLAVORS_COLS,
                             is_unique='id',
                             is_bool=('deleted', ))

    def init(self):
        """
        Initialize the database
        """
        if os.path.exists(CONF.dwarf_db):
            print('Database exists already')
            return

        LOG.info('Initializing database %s', CONF.dwarf_db)
        self.servers.init()
        self.keypairs.init()
        self.images.init()
        self.flavors.init()

        # Hard-code the default flavors
        self.flavors.create(id=100, name='standard.xsmall', ram='512',
                            disk='10', vcpus='1')
        self.flavors.create(id=101, name='standard.small', ram='768',
                            disk='30', vcpus='1')
        self.flavors.create(id=102, name='standard.medium', ram='1024',
                            disk='30', vcpus='1')

    def delete(self):
        """
        Delete the database
        """
        if not os.path.exists(CONF.dwarf_db):
            print('Database does not exist')
            return

        LOG.info('Deleting database %s', CONF.dwarf_db)
        os.remove(CONF.dwarf_db)

    def dump(self, table=None):
        """
        Dump a database table
        """
        if table is None:
            con = sq3.connect(CONF.dwarf_db)
            with con:
                cur = con.cursor()
                cur.execute('SELECT * FROM sqlite_master')
                rows = cur.fetchall()

        else:
            try:
                obj = getattr(self, table)
            except AttributeError:
                print('Table %s not found' % table)
                return
            rows = obj.dump()

        _print_rows(rows)
