# -*- coding: utf-8 -*-
import itertools
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
CLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))

from cheshire3.baseObjects import Session
from cheshire3.exceptions import ObjectDoesNotExistException
from cheshire3.server import SimpleServer

from clic.c3chapter import get_chapter, restore_chapter_cache
from clic.c3wordlist import facets_to_df

class ClicDb():
    def __init__(self):
        """
        Create a CLiC DB instance, connecting to both cheshire3 and the
        relational database.
        """
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

        # Extra lookup tables not available from cheshire data
        with open(os.path.join(CLIC_DIR, 'cheshire3-server', 'dbs', 'extra_data.json')) as f:
            self.extra_data = json.load(f)

    def close(self):
        self.rdb.close()

    def warm_cache(self):
        """
        Load chapters into RAM, this takes ~20s but improves query times
        dramatically
        """
        restore_chapter_cache()

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

    def corpora_list_to_query(self, corpora, db='cheshire'):
        """
        Given a list of books / entire subcorpora, return a query clause
        - db == 'cheshire': Return a CQL where clause string
        - db == 'rdb': Return (SQL where clause, params)
        """
        corpus_names = self.get_corpus_names()
        subcorpus = []
        books = []
        for m in corpora:
            if m in corpus_names:
                subcorpus.append(m)
            else:
                books.append(m)

        if db == 'cheshire':
            return '(' + ' OR '.join(itertools.chain(
                ('c3.subCorpus-idx = "%s"' % s for s in subcorpus),
                ('c3.book-idx = "%s"' % s for s in books),
            )) + ')'

        if db == 'rdb':
            return (" ".join((
                "(",
                "c.book_id IN (SELECT book_id FROM book WHERE corpus_id IN (", ",".join("?" for x in xrange(len(subcorpus))), "))",
                "OR",
                "c.book_id IN (", ",".join("?" for x in xrange(len(books))), ")",
                ")",
            )), subcorpus + books)

        raise ValueError("Unknown db type %s" % db)

    def get_chapter_word_counts(self, book_id, chapter_num):
        """
        For the given book id and chapter, return:
        - count_prev_chap: Word count for all chapters before (chapter)
        - total_word: Total word count in the book
        """
        c = self.rdb.cursor()
        c.execute("SELECT chapter_num, word_total FROM chapter WHERE book_id = ?", (book_id,))

        count_prev_chap = 0
        total_word = 0
        for (c_num, ch_total) in c.fetchall():
            if c_num < chapter_num:
                count_prev_chap += ch_total
            total_word += ch_total
        return (count_prev_chap, total_word)

    def get_chapter(self, chapter_id):
        return get_chapter(self.session, self.recStore, chapter_id)

    def get_subset_index(self, subset):
        """Return the index associated with a subset"""
        return dict(
            shortsus='shortsus-idx',
            longsus='longsus-idx',
            nonquote='non-quote-idx',
            quote='quote-idx',
            all='chapter-idx',
        )[subset]

    def get_word_list(self, subset, cluster_length, corpora):
        """
        Build a Cheshire3WordList word list data frame
        - (subset, cluster_length) form the index to use, e.g.
          'quote', 3 --> 'quote-3-gram-idx'
          '', 1 --> 'chapter-idx'
          'quote', 1 -> 'quote-idx'
        - corpora: Combination of subcorpus names and book names
        """
        index_name = self.get_subset_index(subset)
        if cluster_length > 1:
            if index_name == 'chapter-idx':
                index_name = '%dgram-idx' % (cluster_length)
            else:
                index_name = '%s-%dgram-idx' % (index_name[:-4], cluster_length)

        results = self.c3_query(self.corpora_list_to_query(corpora))
        facets = self.db.get_object(self.session, index_name).facets(self.session, results)

        return facets_to_df(facets)

    def c3_query(self, query):
        return self.db.search(self.session, self.qf.get_query(self.session, query))

    def rdb_query(self, *args):
        c = self.rdb.cursor()
        return c.execute(*args)

    def store_documents(self, doc_dir):
        """
        Store all XML files in (doc_dir) into cheshire3

        doc_dir should be absolute
        """
        db = self.db
        geniaTxr = db.get_object(self.session, 'corpusTransformer')
        indexWF = db.get_object(self.session, 'indexWorkflow')
        recStore = db.get_object(self.session, 'recordStore')
        ampPreP = db.get_object(self.session, 'AmpPreParser')
        xmlp = db.get_object(self.session, 'LxmlParser')
        df = db.get_object(self.session, 'SimpleDocumentFactory')

        df.load(self.session, doc_dir)
        recStore.begin_storing(self.session)
        db.begin_indexing(self.session)
        errorCount= 0
        for i, d in enumerate(df, start=1):
            doc = ampPreP.process_document(self.session, d)
            try:
                rec = xmlp.process_document(self.session, doc)
                genia = geniaTxr.process_record(self.session, rec)
                rec2 = xmlp.process_document(self.session, genia)
                recStore.create_record(self.session, rec2)
                db.add_record(self.session, rec2)
                indexWF.process(self.session, rec2)

                # Index new record in RDB
                self.rdb_index_record(self.recStore.fetch_record(self.session, rec2.id))
            except Exception as e:
                raise
                errorCount += 1
                traceback.print_exc(file=sys.stdout)
        recStore.commit_storing(self.session)
        db.commit_indexing(self.session)
        self.rdb.commit()

    def rdb_index_record(self, record):
        """
        Index the record object within the relational database
        Transactions are not handled, caller is responsible for commits
        """
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

        chapter_id = record.id
        dom = record.dom
        ch_node = dom.xpath('/div')[0]
        chapter_num = int(ch_node.get('num'))
        book_id = ch_node.get('book')
        corpus_id = ch_node.get('subcorpus', '') or self.extra_data['book_corpus'][book_id]
        book_title = ch_node.get('booktitle', '') or self.extra_data['book_titles'][book_id]
        word_count = int(ch_node.xpath("count(descendant::w)"))

        # Insert book-level metadata into DB
        _rdb_insert(c, "corpus", (
            corpus_id,
            self.extra_data['corpus_titles'][corpus_id],
        ));
        _rdb_insert(c, "book", (
            book_id,
            book_title,
            corpus_id,
        ));
        _rdb_insert(c, "chapter", (
            chapter_id,
            book_id,
            chapter_num,
            record.digest,
            word_count,
        ));

        # Index locations of all subsets
        node = dict()
        for n in sorted(dom.xpath('//*[@wordOffset and @eid]'), key=lambda n: int(n.attrib['wordOffset'])):
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
                chapter_id,
                n.attrib['eid'],
                dict(
                    qs='nonquote',
                    qe='quote',
                    sle='longsus',
                    sse='shortsus',
                )[n.tag],
                0 if start_node is None else int(start_node.attrib['wordOffset']),
                int(n.attrib['wordOffset']),
            ))

        # Trigger chapter indexing
        self.get_chapter(chapter_id)

        if 'qe' in node:
            # End of quote up until end of text is non-quote
            _rdb_insert(c, "subset", (
                chapter_id,
                node['qe'].attrib['eid'],
                'nonquote',
                node['qe'].attrib['wordOffset'],
                word_count,
            ))

    def recreate_rdb(self):
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
            chapter_id INT,
            book_id TEXT,
            chapter_num INT NOT NULL,
            c3_digest TEXT NOT NULL,
            word_total INT NOT NULL,
            FOREIGN KEY(book_id) REFERENCES book(book_id),
            PRIMARY KEY (chapter_id)
        )''')
        c.execute('''CREATE TABLE subset (
            chapter_id INT,
            eid INT,
            subset_type TEXT,
            offset_start INT NOT NULL,
            offset_end INT NOT NULL,
            FOREIGN KEY(chapter_id) REFERENCES chapter(chapter_id),
            PRIMARY KEY (chapter_id, eid)
        )''')

        chapter_id = 0
        while True:
            try:
                record = self.recStore.fetch_record(self.session, chapter_id)
            except ObjectDoesNotExistException:
                break
            self.index_record(record)
            yield "Cached %d %s %s chapter %d" % (chapter_id, corpus_id, book_id, chapter_num)
            chapter_id += 1
        yield "Committing..."
        self.rdb.commit()


if __name__ == '__main__':
    cdb = ClicDb()
    for o in cdb.recreate_rdb():
        print(o)
