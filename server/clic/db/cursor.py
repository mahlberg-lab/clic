import contextlib
import os
import logging
import time
import threading

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import MinTimeLoggingConnection as BaseLoggingConnection

import appconfig

_pool = None
_pool_lock = threading.Lock()

logger = logging.getLogger(__name__)
explain_logger = logging.getLogger(__name__ + '.explain')
if os.environ.get('QUERY_LOG', False):
    logging.basicConfig(level=logging.DEBUG)
    if os.environ['QUERY_LOG'] == 'explain':
        explain_logger.setLevel(logging.ERROR)


class LoggingConnection(BaseLoggingConnection):
    def filter(self, msg, cur):
        if msg:  # NB: msg == None is probably an error, but don't mask it with our own
            msg = "%.5fms: %s" % (
                (time.time() - cur.timestamp) * 1000,  # NB: cur.timestamp comes from using MinTimeLoggingConnection
                msg.decode('utf8'),  # String so loggers know how to print it
            )
        if explain_logger.isEnabledFor(logging.DEBUG):
            if msg.startswith("EXPLAIN "):
                return None  # Avoid infinite recursion
            explain_cur = cur.connection.cursor()
            explain_cur.execute("EXPLAIN " + msg)
            explain_logger.debug("\n" + "\n".join(x[0] for x in explain_cur.fetchall()))
        return msg


def get_pool_cursor():
    """
    Returns a cursor pointing at a DB connection from our pool. You should call
    put_pool_cursor() to put it back again when done.
    """
    global _pool

    if _pool is None:
        # Connection pool not ready yet, create. pool_lock prevents
        # multiple threads trying to do this at the same time.
        with _pool_lock:
            if _pool is None:
                _pool = ThreadedConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=os.environ.get('DB_DSN', appconfig.DB_DSN),
                    connection_factory=LoggingConnection
                )

    conn = _pool.getconn()
    conn.initialize(logger)
    conn.set_session(readonly=True)
    return conn.cursor()


def put_pool_cursor(cur):
    """
    Closes (cur) and returns it's associated connection back to the pool
    """
    conn = cur.connection
    # NB: We don't support writing to DB within connection pools, so just rollback
    conn.rollback()
    cur.close()
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
