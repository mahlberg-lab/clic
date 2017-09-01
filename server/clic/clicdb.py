# -*- coding: utf-8 -*-
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
CLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

from cheshire3.baseObjects import Session
from cheshire3.exceptions import ObjectDoesNotExistException
from cheshire3.server import SimpleServer

from clic.c3chapter import get_chapter

class ClicDb():
    def __init__(self):
        self.session = Session()
        self.session.database = 'db_dickens'
        server = SimpleServer(
            self.session,
            os.path.join(CLIC_DIR, 'cheshire3-server', 'configs', 'serverConfig.xml')
        )
        self.db = server.get_object(self.session, self.session.database)
        self.qf = self.db.get_object(self.session, 'defaultQueryFactory')
        self.recStore = self.db.get_object(self.session, 'recordStore')
        self.idxStore = self.db.get_object(self.session, 'indexStore')

        self.rdb = sqlite3.connect(os.path.join(CLIC_DIR, 'cheshire3-server', 'dbs', 'c3.sqlite'))

    def close(self):
        self.rdb.close()

    def get_corpus_names(self):
        """Return a list of valid corpus names"""
        return [
            x.queryTerm
            for x
            in self.idxStore.get_object(self.idxStore.session, 'subCorpus-idx')
        ]

    def get_corpus_structure(self):
        """
        Return a list of dicts containing:
        - id: corpus short name
        - title: corpus title
        - children: [{id: book id, title: book title}, ...]
        """
        c = self.rdb.cursor()
        c.execute("SELECT c.corpus_id, c.title, b.book_id, b.title FROM corpus c, book b WHERE b.corpus_id = c.corpus_id ORDER BY c.title, b.title")

        out = []
        for (c_id, c_title, b_id, b_title) in c.fetchall():
            if len(out) == 0 or out[-1]['id'] != c_id:
                out.append(dict(id=c_id, title=c_title, children=[]))
            out[-1]['children'].append(dict(id=b_id, title=b_title))
        return out

    def get_chapter_word_counts(self, book_id, chapter):
        """
        For the given book id and chapter, return:
        - count_prev_chap: Word count for all chapters before (chapter)
        - total_word: Total word count in the book
        """
        c = self.rdb.cursor()
        c.execute("SELECT chapter_id, word_total FROM chapter WHERE book_id = ?", (book_id,))

        count_prev_chap = 0
        total_word = 0
        for (chapter_id, ch_total) in c.fetchall():
            if chapter_id < chapter:
                count_prev_chap += ch_total
            total_word += ch_total
        return (count_prev_chap, total_word)

    def get_chapter(self, chapter_id):
        return get_chapter(self.session, self.recStore, chapter_id)

    def c3_query(self, query):
        return self.db.search(self.session, self.qf.get_query(self.session, query))

    def recreate_rdb(self):
        def _rdb_insert(c, table, rec, ignoreDuplicate=True):
            try:
                c.execute("INSERT INTO %s VALUES (%s)" % (
                    table,
                    ",".join("?" for x in xrange(len(rec)))
                ), rec)
            except sqlite3.IntegrityError as e:
                if not ignoreDuplicate or not e.message.startswith('UNIQUE constraint'):
                    raise

        c = self.rdb.cursor()
        c.execute('''CREATE TABLE corpus (
            corpus_id TEXT,
            title TEXT NOT NULL,
            PRIMARY KEY (corpus_id)
        )''')
        c.execute('''CREATE TABLE book (
            book_id,
            title TEXT NOT NULL,
            corpus_id TEXT,
            FOREIGN KEY(corpus_id) REFERENCES corpus(corpus_id),
            PRIMARY KEY (book_id)
        )''')
        c.execute('''CREATE TABLE chapter (
            book_id TEXT,
            chapter_id INT,
            c3_digest TEXT NOT NULL,
            word_total INT NOT NULL,
            FOREIGN KEY(book_id) REFERENCES book(book_id),
            PRIMARY KEY (book_id, chapter_id)
        )''')
        c.execute('''CREATE TABLE subset (
            book_id TEXT,
            chapter_id INT,
            eid INT,
            subset_type TEXT,
            offset_start INT NOT NULL,
            offset_end INT NOT NULL,
            FOREIGN KEY(book_id) REFERENCES book(book_id),
            PRIMARY KEY (book_id, chapter_id, eid)
        )''')

        # Extra lookup tables not available from cheshire data
        with open(os.path.join(CLIC_DIR, 'cheshire3-server', 'dbs', 'extra_data.json')) as f:
            extra_data = json.load(f)

        rec_id = 0
        while True:
            try:
                record = self.recStore.fetch_record(self.session, rec_id)
            except ObjectDoesNotExistException:
                break
            dom = record.dom
            ch_node = dom.xpath('/div')[0]
            chapter_id = int(ch_node.get('num'))
            book_id = ch_node.get('book')
            corpus_id = ch_node.get('corpus', extra_data['book_corpus'][book_id])
            word_count = int(ch_node.xpath("count(descendant::w)"))

            _rdb_insert(c, "corpus", (
                corpus_id,
                extra_data['corpus_titles'][corpus_id],
            ));
            _rdb_insert(c, "book", (
                book_id,
                extra_data['book_titles'][book_id],
                corpus_id,
            ));
            _rdb_insert(c, "chapter", (
                book_id,
                chapter_id,
                record.digest,
                word_count,
            ));

            node = dict()
            for n in sorted(dom.xpath('//*[@wordOffset and @eid]'), key=lambda n: n.attrib['wordOffset']):
                node[n.tag] = n
                if n.tag in ['qs']:
                    # Start of a quote, thus up to the last qe is a non-quote
                    start_node = node.get('qe', None)
                elif n.tag.endswith('e'):
                    # End of a subset
                    start_node = node.get(n.tag[0:-1] + 's', None)
                else:
                    # Not the end of a subset, move on
                    continue

                _rdb_insert(c, "subset", (
                    book_id,
                    chapter_id,
                    n.attrib['eid'],
                    dict(
                        qs='nonquote',
                        qe='quote',
                        sle='longsus',
                        sse='shortsus',
                    )[n.tag],
                    0 if start_node is None else start_node.attrib['wordOffset'],
                    n.attrib['wordOffset'],
                ))

            if node.get('qe', None):
                # End of quote up until end of text is non-quote
                _rdb_insert(c, "subset", (
                    book_id,
                    chapter_id,
                    node['qe'].attrib['eid'],
                    'nonquote',
                    node['qe'].attrib['wordOffset'],
                    word_count,
                ))

            yield "Cached %d %s %s chapter %d" % (rec_id, corpus_id, book_id, chapter_id)
            rec_id += 1
        yield "Committing..."
        self.rdb.commit()


if __name__ == '__main__':
    cdb = ClicDb()
    for o in cdb.recreate_rdb():
        print(o)
