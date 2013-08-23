#!/usr/bin/python

import bottle
import logging
import threading

from dwarf import db as dwarf_db
from dwarf import exception
from dwarf import http

from dwarf.common import config

CONF = config.CONFIG
LOG = logging.getLogger(__name__)


def _to_string(objs):
    result = []
    for obj in objs:
        result.append(' | '.join(str(o) for o in obj))
    return '\n'.join(result) + '\n'


class DatabaseApiThread(threading.Thread):
    server = None

    def stop(self):
        self.server.stop()

    def run(self):
        """
        Database API thread worker
        """
        LOG.info('Starting database API worker')

        db = dwarf_db.Controller()
        app = bottle.Bottle()

        @app.get('/db')
        @app.post('/db')
        @exception.catchall
        def http_1():   # pylint: disable=W0612
            """
            Dump or initialize the database
            """
            # Initialize the database
            if bottle.request.method == 'POST':
                db.delete()
                db.init()
                return 'Database initialized\n'

            # Dump the master database
            else:
                return _to_string(db.dump())

        @app.get('/db/<table>')
        @exception.catchall
        def http_2(table):   # pylint: disable=W0612
            """
            Dump a single database table
            """
            # Dump a single database table
            obj = getattr(db, table, None)
            if not obj:
                raise exception.Failure(reason='Table %s does not exist' %
                                        table, code=400)

            return _to_string(obj.dump())

        @app.delete('/db/<table>/<rid>')
        @exception.catchall
        def http_3(table, rid):   # pylint: disable=W0612
            """
            Delete a table row
            """
            # Delete a table row
            obj = getattr(db, table, None)
            if not obj:
                raise exception.Failure(reason='Table %s does not exist' %
                                        table, code=400)
            obj.delete(id=rid)

        host = '127.0.0.1'
        port = CONF.database_api_port
        self.server = http.BaseHTTPServer(host=host, port=port)

        LOG.info('Database API server listening on %s:%s', host, port)
        bottle.run(app, server=self.server)
        LOG.info('Database API server shut down')
