import contextlib
import os

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

_cur_dsn = None
_pool = None


@contextlib.contextmanager
def get_pool_cursor():
    global _pool, _cur_dsn
    dsn = os.environ['DB_DSN']
    if _cur_dsn != dsn:
        _pool = ThreadedConnectionPool(1, 10, dsn=dsn)
        _cur_dsn = dsn  # TODO: Can we get DSN out of _pool object?
    conn = _pool.getconn()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.rollback()
        _pool.putconn(conn)


@contextlib.contextmanager
def get_script_cursor():
    """Return a single cursor for a short-lived script"""
    dsn = os.environ['DB_DSN']
    conn = psycopg2.connect(dsn)
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.rollback()
        conn.close()
