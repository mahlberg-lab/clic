import os
import subprocess

import psycopg2

import testing.postgresql


def runSqlScript(postgresql, script):
    out = subprocess.run((
        'psql', '-b',
        '-f', script,
        '-h', 'localhost',
        '-p', str(postgresql.settings['port']),
        '-U', 'postgres', '-w',
        'test',
    ), check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if b'ERROR' in out.stderr:
        raise ValueError("Running " + script + " failed:\n" + out.stderr.decode('utf8'))
    return out.stdout + out.stderr


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

    def put_books(self, **book_contents):
        """
        Put all books in DB, using default taggers.
        - **book_contents: dict of book name -> contents
        """
        from clic.region.tag import tagger
        from clic.db.book import put_book

        cur = self.pg_cur()

        for book_name, content in book_contents.items():
            book = dict(name=book_name, content=content)
            tagger(book)
            put_book(cur, book)

    def put_corpora(self, *corpus):
        """
        Add a list of corpora to DB
        """
        from clic.db.corpus import put_corpus

        cur = self.pg_cur()

        for i, c in enumerate(corpus):
            c['ordering'] = c.get('ordering', i)
            c['title'] = c.get('title', "UT corpus %s" % c['name'])
            put_corpus(cur, c)
