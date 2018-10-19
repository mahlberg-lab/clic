import os
import subprocess

import psycopg2

import testing.postgresql


def runSqlScript(postgresql, script):
    return subprocess.run((
        'psql', '-b',
        '-f', script,
        '-h', 'localhost',
        '-p', str(postgresql.settings['port']),
        '-U', 'postgres', '-w',
        'test',
    ), check=True, stdout=subprocess.PIPE).stdout


def initDatabase(postgresql):
    dir = '../schema'
    out = []
    for s in sorted(os.listdir(dir)):
        if not s.endswith('.sql'):
            continue
        out.append(runSqlScript(postgresql, os.path.join(dir, s)))
    return b''.join(out)


Postgresql = testing.postgresql.PostgresqlFactory(
    cache_initialized_db=True,
    on_initialized=initDatabase,
)


class RequiresPostgresql():
    @classmethod
    def setUpClass(cls):
        super(RequiresPostgresql, cls).setUpClass()

        cls.postgresql = Postgresql()

    def tearDown(self):
        for cur in getattr(self, '_pg_curs', []):
            cur.close()

        if hasattr(self, 'pg_conn'):
            self.pg_conn.close()

        super(RequiresPostgresql, self).tearDown()

    @classmethod
    def tearDownClass(cls):
        cls.postgresql.stop()
        del cls.postgresql

        super(RequiresPostgresql, cls).tearDownClass()

    def pg_cur(self):
        """
        Get a new cursor for the unittest database, it will be closed
        on test tearDown
        """
        if not hasattr(self, 'pg_conn'):
            self.pg_conn = psycopg2.connect(**self.postgresql.dsn())
        if not getattr(self, '_pg_curs', []):
            self._pg_curs = []
        self._pg_curs.append(self.pg_conn.cursor())
        return self._pg_curs[-1]

    def put_book(self, content, regions=None):
        from hashlib import sha1
        from clic.db.book import put_book

        cur = self.pg_cur()
        if not regions:
            # Minimum-viable list of regions
            regions = [
                ['chapter.text', 1, 0, len(content)],
                ['chapter.paragraph', 1, 0, len(content)],
                ['chapter.sentence', 1, 0, len(content)],
            ]

        book_name = sha1(content.encode('utf8')).hexdigest()[-10:]
        put_book(cur, dict(
            name=book_name,
            content=content,
            regions=regions,
        ))
        return book_name
