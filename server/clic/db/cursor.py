import contextlib
import os
import logging

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import LoggingConnection as BaseLoggingConnection

import appconfig

_pool = None

logger = logging.getLogger(__name__)
explain_logger = logging.getLogger(__name__ + '.explain')
if os.environ.get('QUERY_LOG', False):
    logging.basicConfig(level=logging.DEBUG)


class LoggingConnection(BaseLoggingConnection):
    def filter(self, msg, cur):
        if msg:  # NB: msg == None is probably an error, but don't mask it with our own
            msg = msg.decode('utf8')  # String so loggers know how to print it
        if explain_logger.isEnabledFor(logging.DEBUG):
            if msg.startswith("EXPLAIN "):
                return None  # Avoid infinite recursion
            explain_cur = cur.connection.cursor()
            explain_cur.execute("EXPLAIN " + msg)
            explain_logger.debug("\n" + "\n".join(x[0] for x in explain_cur.fetchall()))
        return msg


@contextlib.contextmanager
def get_pool_cursor():
    global _pool
    dsn = os.environ.get('DB_DSN', appconfig.DB_DSN)
    if not _pool or dsn != _pool._kwargs['dsn']:
        _pool = ThreadedConnectionPool(1, 10, dsn=dsn, connection_factory=LoggingConnection)
    conn = _pool.getconn()
    try:
        conn.initialize(logger)
        yield conn.cursor()
        conn.commit()
    finally:
        conn.rollback()
        _pool.putconn(conn)


@contextlib.contextmanager
def get_script_cursor(for_write=False):
    """Return a single cursor for a short-lived script"""
    dsn = os.environ.get('DB_DSN', appconfig.DB_DSN)
    conn = psycopg2.connect(dsn, connection_factory=LoggingConnection)
    conn.initialize(logger)
    conn.set_session(readonly=not(for_write))
    try:
        yield conn.cursor()
        conn.commit()
        if for_write:
            # If writing, vaccuum afterwards
            conn.set_session(autocommit=True)
            cur = conn.cursor()
            cur.execute("VACUUM ANALYSE")
    finally:
        conn.rollback()
    conn.close()
