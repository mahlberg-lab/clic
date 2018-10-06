import contextlib
import os

import psycopg2
from psycopg2.pool import ThreadedConnectionPool

_pool = None


@contextlib.contextmanager
def get_pool_cursor():
    global _pool
    dsn = os.environ['DB_DSN']
    if not _pool or dsn != _pool._kwargs['dsn']:
        _pool = ThreadedConnectionPool(1, 10, dsn=dsn)
    conn = _pool.getconn()
    try:
        yield conn.cursor()
        conn.commit()
    finally:
        conn.rollback()
        _pool.putconn(conn)


@contextlib.contextmanager
def get_script_cursor(for_write=False):
    """Return a single cursor for a short-lived script"""
    dsn = os.environ['DB_DSN']
    conn = psycopg2.connect(dsn)
    conn.set_session(readonly=not(for_write))
    try:
        yield conn.cursor()
        conn.commit()
        if for_write:
            # If writing, vaccuum and rebuild views afterwards
            conn.set_session(autocommit=True)
            cur = conn.cursor()
            cur.execute("VACUUM ANALYSE")
            cur.execute("SELECT refresh_book_materialized_views()")
    finally:
        conn.rollback()
    conn.close()
