#!/usr/bin/python

import bottle
import logging
import threading

from wsgiref.simple_server import WSGIRequestHandler

from dwarf import db
from dwarf import exception

LOG = logging.getLogger(__name__)


def _to_string(objs):
    result = []
    for obj in objs:
        result.append(' | '.join(str(o) for o in obj))
    return '\n'.join(result) + '\n'


class DatabaseApiRequestHandler(WSGIRequestHandler):
    def log_message(self, fmt, *args):
        LOG.info(fmt, *args)


class DatabaseApiThread(threading.Thread):

    def __init__(self, port):
        threading.Thread.__init__(self)
        self.port = port
        self.db = db.Controller()

    def run(self):
        LOG.info('Starting database API thread')

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
                self.db.delete()
                self.db.init()
                return 'Database initialized\n'

            # Dump the master database
            else:
                return _to_string(self.db.dump())

        @app.get('/db/<table>')
        @exception.catchall
        def http_table(table):   # pylint: disable=W0612
            """
            Dump a single database table
            """
            # Dump a single database table
            obj = getattr(self.db, table, None)
            if not obj:
                raise exception.Failure(reason='Table %s does not exist' %
                                        table,
                                        code=400)

            return _to_string(obj.dump())

        bottle.run(app, host='127.0.0.1', port=self.port,
                   handler_class=DatabaseApiRequestHandler)
