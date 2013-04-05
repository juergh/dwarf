#!/usr/bin/python

from __future__ import print_function

import os
import sqlite3 as sq3

from dwarfclient import exception

from dwarfclient.common import config
from dwarfclient.common import log

CONF = config.CONF
LOG = log.LOG


class Controller(object):

    def __init__(self, args):
        self.args = args

    def init(self):
        """
        Initialize the Dwarf database
        """
        LOG.debug('db.init')

        if os.path.exists(CONF.dwarf_db):
            print('Database exists already')
            return

        con = sq3.connect(CONF.dwarf_db)
        with con:
            cur = con.cursor()
            cur.execute('CREATE TABLE servers(id INT, name TEXT)')

    def delete(self):
        """
        Delete the Dwarf database
        """
        LOG.debug('db.delete')

        if os.path.exists(CONF.dwarf_db):
            print('Are you sure you want to delete the database [y/N]: ',
                  end='')
            choice = raw_input().lower()
            if choice in ['y', 'yes']:
                os.remove(CONF.dwarf_db)

    def dump(self, table=None):
        """
        Dump the Dwarf database
        """
        LOG.debug('db.dump: table=%s', table)

        if table is None:
            table = 'sqlite_master'

        con = sq3.connect(CONF.dwarf_db)
        with con:
            cur = con.cursor()
            print("table '%s':" % table)
            cur.execute('SELECT * FROM %s' % table)
            for row in cur.fetchall():
                print(row)

    def init_server(self, name):
        """
        Initialize a new server row and return it
        """
        LOG.debug("db.init_server: name='%s'", name)

        sid = 1
        con = sq3.connect(CONF.dwarf_db)
        with con:
            cur = con.cursor()

            # Check if the name exists already
            cur.execute("SELECT * FROM servers WHERE name='%s'" % name)
            row = cur.fetchone()
            if row:
                raise exception.DwarfException("A server with name '%s' "
                                               "exists already" % name)

            # Get the highest ID
            cur.execute('SELECT max(id) FROM servers')
            row = cur.fetchone()
            if row[0] is not None:
                sid = row[0] + 1

            # Add the new row
            cur.execute("INSERT INTO servers VALUES(%d, '%s')" % (sid, name))

        LOG.debug('db.init_server: new server ID is %d', sid)
        return self.get_server(sid)

    def delete_server(self, sid):
        """
        Delete a server row
        """
        LOG.debug('db.delete_server: server=%d', sid)

        con = sq3.connect(CONF.dwarf_db)
        with con:
            cur = con.cursor()
            cur.execute('DELETE FROM servers WHERE id=%d' % sid)

    def get_server_list(self):
        """
        Return an array with server details dicts
        """
        LOG.debug('db.get_server_list')

        servers = []
        con = sq3.connect(CONF.dwarf_db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM servers')
            rows = cur.fetchall()

        # Convert to an array of dicts and return
        for row in rows:
            servers.append(dict(zip(row.keys(), row)))
        return servers

    def get_server(self, sid):
        """
        Return a dict with the server details
        """
        LOG.debug('db.get_server: server=%d', sid)

        con = sq3.connect(CONF.dwarf_db)
        with con:
            con.row_factory = sq3.Row
            cur = con.cursor()
            cur.execute('SELECT * FROM servers WHERE id=%d' % sid)
            row = cur.fetchone()

        if not row:
            raise exception.DwarfException("No server with ID '%d' exists" %
                                           sid)
        # Convert to a dict and return
        return dict(zip(row.keys(), row))
