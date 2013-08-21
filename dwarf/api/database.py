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


def _to_string(objs):
    result = []
    for obj in objs:
        result.append(' | '.join(str(o) for o in obj))
    return '\n'.join(result) + '\n'


def _database_api_worker():
    """
    Database API thread worker
    """
    LOG.info('Starting database API worker')

    db = dwarf_db.Controller()
    app = bottle.Bottle()

    @app.get('/db')
    @app.post('/db')
    @exception.catchall
    def http_db():   # pylint: disable=W0612
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
    def http_table(table):   # pylint: disable=W0612
        """
        Dump a single database table
        """
        # Dump a single database table
        obj = getattr(db, table, None)
        if not obj:
            raise exception.Failure(reason='Table %s does not exist' % table,
                                    code=400)

        return _to_string(obj.dump())

    @app.delete('/db/<table>/<rid>')
    @exception.catchall
    def http_table_id(table, rid):   # pylint: disable=W0612
        """
        Delete a table row
        """
        # Delete a table row
        obj = getattr(db, table, None)
        if not obj:
            raise exception.Failure(reason='Table %s does not exist' % table,
                                    code=400)
        obj.delete(id=rid)

    host = '127.0.0.1'
    port = CONF.database_api_port
    LOG.info('Database API server listening on %s:%s', host, port)
    bottle.run(app, host=host, port=port,
               handler_class=utils.BottleRequestHandler)


def thread():
    """
    Return the database API thread
    """
    return threading.Thread(target=_database_api_worker)
