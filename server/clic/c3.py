# -*- coding: utf-8 -*-
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
CLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

from cheshire3.baseObjects import Session
from cheshire3.exceptions import ObjectDoesNotExistException
from cheshire3.server import SimpleServer

session = Session()
session.database = 'db_dickens'

rdb = sqlite3.connect(os.path.join(CLIC_DIR, 'cheshire3-server', 'dbs', 'c3.sqlite'))

server = SimpleServer(
    session,
    os.path.join(CLIC_DIR, 'cheshire3-server', 'configs', 'serverConfig.xml')
)
db = server.get_object(session, session.database)
qf = db.get_object(session, 'defaultQueryFactory')
recStore = db.get_object(session, 'recordStore')
idxStore = db.get_object(session, 'indexStore')
#logger = db.get_object(session, 'concordanceLogger')

def get_corpus_names():
    """Return a list of valid corpus names"""
    return [
        x.queryTerm
        for x
        in idxStore.get_object(idxStore.session, 'subCorpus-idx')
    ]


def get_chapter_word_counts(book_id, chapter):
    """
    For the given book id and chapter, return:
    - count_prev_chap: Word count for all chapters before (chapter)
    - total_word: Total word count in the book
    """
    c = rdb.cursor()
    c.execute("SELECT chapter_id, word_total FROM chapter WHERE book_id = ?", (book_id,))

    count_prev_chap = 0
    total_word = 0
    for (chapter_id, ch_total) in c.fetchall():
        if chapter_id < chapter:
            count_prev_chap += ch_total
        total_word += ch_total
    return (count_prev_chap, total_word)

def _rdb_insert(c, table, rec, ignoreDuplicate=True):
    try:
        c.execute("INSERT INTO %s VALUES (%s)" % (
            table,
            ",".join("?" for x in xrange(len(rec)))
        ), rec)
    except sqlite3.IntegrityError as e:
        if not ignoreDuplicate or not e.message.startswith('UNIQUE constraint'):
            raise

def recreate_rdb():
    c = rdb.cursor()
    c.execute('''CREATE TABLE corpus (
        corpus_id TEXT,
        corpus_title TEXT NOT NULL,
        PRIMARY KEY (corpus_id)
    )''')
    c.execute('''CREATE TABLE book (
        book_id,
        book_title TEXT NOT NULL,
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

    # Extra lookup tables not available from cheshire data
    with open(os.path.join(CLIC_DIR, 'cheshire3-server', 'dbs', 'extra_data.json')) as f:
        extra_data = json.load(f)

    rec_id = 0
    while True:
        try:
            record = recStore.fetch_record(session, rec_id)
        except ObjectDoesNotExistException:
            break
        dom = record.dom
        ch_node = dom.xpath('/div')[0]
        chapter_id = int(ch_node.get('num'))
        book_id = ch_node.get('book')
        corpus_id = ch_node.get('corpus', extra_data['book_corpus'][book_id])

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
            int(ch_node.xpath("count(descendant::w)")),
        ));
        yield "Cached %d %s %s chapter %d" % (rec_id, corpus_id, book_id, chapter_id)
        rec_id += 1
    yield "Committing..."
    rdb.commit()


if __name__ == '__main__':
    for o in recreate_rdb():
        print(o)
