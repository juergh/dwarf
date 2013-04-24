#!/usr/bin/python

from __future__ import print_function

import os
import sqlite3 as sq3

from dwarf import exception

from dwarf.common import config

CONFIG = config.CONFIG


def _dump_table(name):
    """
    Return all table rows
    """
    con = sq3.connect(CONFIG.dwarf_db)
    with con:
        cur = con.cursor()
        cur.execute('SELECT * FROM %s' % name)
        rows = cur.fetchall()
    return rows


class Table(object):

    def __init__(self, table, cols):
        self.table = table
        self.cols = cols

    def init(self):
        """
        Initialize (create) the table
        """
        # Convert the cols array to an sqlite formatting string, i.e.,:
        # 'id TEXT, name TEXT, status TEXT, key TEXT'
        fmt = ','.join(['%s TEXT' % c for c in self.cols])

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            cur = con.cursor()
            cur.execute('CREATE TABLE %s (%s)' % (self.table, fmt))

    def dump(self):
        """
        Return all table rows
        """
        return _dump_table(self.table)

    def add(self, **kwargs):
        """
        Add a new table row
        """
        print('db.%s.add()' % self.table)
        name = kwargs.get('name')

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            cur = con.cursor()
            if name:
                # Check if the row exists already
                cur.execute('SELECT * FROM %s WHERE name=?' % self.table,
                            (name, ))
                if cur.fetchone():
                    raise exception.Failure(reason='%s %s already exists' %
                                            (self.table.rstrip('s'), name),
                                            code=400)

            if 'id' in self.cols:
                # Get the highest row ID
                kwargs['id'] = 1
                cur.execute('SELECT max(id) FROM %s' % self.table)
                row = cur.fetchone()
                if row[0] is not None:
                    kwargs['id'] = int(row[0]) + 1

            # Create the array of table row values (in the right column order)
            vals = []
            for c in self.cols:
                vals.append(kwargs.get(c, None))

            # Create the sqlite formatting string, i.e., '?,?,?,?'
            fmt = ('?,' * len(self.cols)).rstrip(',')

            # Insert the new row
            cur.execute('INSERT into %s values (%s)' % (self.table, fmt), vals)

    def delete(self, **kwargs):
        """
        Delete a table row
        """
        print('db.%s.delete()' % self.table)
        name = kwargs.get('name')

        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            cur = con.cursor()

            # Check if the row exists
            cur.execute('SELECT * FROM %s WHERE name=?' % self.table, (name, ))
            if not cur.fetchone():
                raise exception.Failure(reason='%s %s not found' %
                                        (self.table.rstrip('s'), name),
                                        code=404)

            # Delete the row
            cur.execute('DELETE FROM %s WHERE name=?' % self.table, (name, ))

    def list(self):
        """
        Get all table rows, converted to an array of dicts
        """
        con = sq3.connect(CONFIG.dwarf_db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM %s' % self.table)
            sq3_rows = cur.fetchall()

        # Convert to an array of dicts
        rows = []
        for row in sq3_rows:
            rows.append(dict(zip(row.keys(), row)))

        return rows

    def details(self, **kwargs):
        """
        Get a single table row, converted to a dict
        """
        pass


class Controller(object):

    def __init__(self):
        self.servers = Table('servers', ['id', 'name', 'status', 'key'])
        self.keypairs = Table('keypairs', ['name', 'fingerprint',
                                           'public_key'])

    def init(self):
        if os.path.exists(CONFIG.dwarf_db):
            print('Database exists already')
            return
        self.servers.init()
        self.keypairs.init()

    def delete(self):
        if not os.path.exists(CONFIG.dwarf_db):
            print('Database does not exist')
            return
        os.remove(CONFIG.dwarf_db)

    def dump(self, table=None):
        if not table:
            return _dump_table('sqlite_master')

        try:
            obj = getattr(self, table)
        except AttributeError:
            return 'Table %s not found' % table

        return obj.dump()
