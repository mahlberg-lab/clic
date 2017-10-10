# -*- coding: utf-8 -*-
import itertools
import json
import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
CLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..'))
C3_SQLITE = "%s" % os.path.join(CLIC_DIR, 'cheshire3-server', 'dbs', 'dickens', 'c3.sqlite')

from cheshire3.baseObjects import Session
from cheshire3.exceptions import ObjectDoesNotExistException
from cheshire3.server import SimpleServer

from clic.c3chapter import get_chapter, restore_chapter_cache, dump_chapter_cache
from clic.errors import UserError


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

        self.rdb = sqlite3.connect(C3_SQLITE)

        # Extra lookup tables not available from cheshire data
        with open(os.path.join(CLIC_DIR, 'cheshire3-server', 'dbs', 'dickens', 'extra_data.json')) as f:
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

    def get_chapter_word_counts(self, chapter_id):
        """
        For the given book id and chapter, return:
        - book_id: The short name of the book
        - chapter_num: The count of the chapter within the book
        - count_prev_chap: Word count for all chapters before (chapter)
        - total_word: Total word count in the book
        """
        (book_id, chapter_num) = self.rdb_query("SELECT book_id, chapter_num FROM chapter WHERE chapter_id = ? ", (chapter_id,)).fetchone()

        count_prev_chap = 0
        total_word = 0
        for (c_num, ch_total) in self.rdb_query("SELECT chapter_num, word_total FROM chapter WHERE book_id = ?", (book_id,)):
            if c_num < chapter_num:
                count_prev_chap += ch_total
            total_word += ch_total
        return (book_id, chapter_id, count_prev_chap, total_word)

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

        if index_name == 'shortsus-5gram-idx':
            raise UserError("Short suspensions are 4 or less words, a 5gram is impossible", "error")

        results = self.c3_query(self.corpora_list_to_query(corpora))
        facets = self.db.get_object(self.session, index_name).facets(self.session, results)
        return facets

    def get_word(self, chapter_id, match):
        """
        Given a chapter_id and CLiC proxInfo match, return an array of:
        - word_id: word position in chapter
        - para_chap: word's paragraph position in chapter
        - sent_chap: word's sentence position in chapter
        """
        # Each time a search term is found in a ProximityIndex
        # (each match) is described in terms of a proxInfo.
        #
        # [[[0, 169, 1033, 15292]],
        #  [[0, 171, 1045, 15292]], etc. ]
        #
        # * the first item is the id of the root element from
        #   which to start counting to find the word node
        #   for instance, 0 for a chapter view (because the chapter
        #   is the root element), but 151 for a search in quotes
        #   text.
        # * the second item in the deepest list (169, 171)
        #   is the id of the <w> (word) node
        # * the third element is the exact character (spaces, and
        #   and punctuation (stored in <n> (non-word) nodes
        #   at which the search term starts
        # * the fourth element is the total amount of characters
        #   in the document?
        #
        # See:-
        # dbs/dickens/dickensConfigs.d/dickensIdxs.xml
        # cheshire3.index.ProximityIndex
        #
        # It's [nodeIdx, wordIdx, offset, termId(?)] in transformer.py

        #NB: cheshire source suggests that there's never multiple, but I can't say for sure
        eid, word_id = match[0][0:2]
        if eid > 0:
            # Look up eid offset and add it to word_id
            # TODO: The query has no index backing it
            subset_offset = self.rdb_query("SELECT offset_start, subset_type FROM subset WHERE chapter_id = ? AND eid = ?", (chapter_id, eid)).fetchone()
            if subset_offset is None:
                raise ValueError("No eid for %d" % eid)
            word_id += subset_offset[0]

        # Find sentence position
        sent_pos = self.rdb_query(
            "SELECT para_id, sent_id" +
            " FROM sentence" +
            " WHERE chapter_id = ?" +
            " AND ? BETWEEN offset_start and offset_end", (chapter_id, word_id)).fetchone()
        if sent_pos is None:
            raise ValueError("Cannot find a sentence in chapter %d containing %d" % (chapter_id, word_id))
        return (word_id, sent_pos[0], sent_pos[1])

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
                yield "Indexed %d" % i
            except Exception as e:
                import traceback

                yield "Failed to index %d:-\n%s" % (
                    i,
                    traceback.format_exc(),
                )
        yield "Committing..."
        recStore.commit_storing(self.session)
        db.commit_indexing(self.session)
        self.rdb.commit()
        yield "Dumping chapter cache..."
        dump_chapter_cache()

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
        book_author = ch_node.get('bookauthor', '') or self.extra_data['book_authors'].get(book_id, '')
        word_count = int(ch_node.xpath("count(descendant::w)"))

        # Insert book-level metadata into DB
        _rdb_insert(c, "corpus", (
            corpus_id,
            self.extra_data['corpus_titles'][corpus_id],
        ));
        _rdb_insert(c, "book", (
            book_id,
            book_title,
            book_author,
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
                0 if start_node is None else start_node.attrib['eid'],
                dict(
                    qs='nonquote',
                    qe='quote',
                    sle='longsus',
                    sse='shortsus',
                )[n.tag],
                0 if start_node is None else int(start_node.attrib['wordOffset']),
                int(n.attrib['wordOffset']),
            ))

        # Index lengths of all paragraphs/sentences
        para_id = 0
        total_count = 0
        for para_node in dom.xpath("/div/p"):
            sent_id = 0
            for sentence_node in para_node.xpath("s"):
                word_count = int(sentence_node.xpath("count(descendant::w)"))
                _rdb_insert(c, "sentence", (
                    chapter_id,
                    para_id,
                    sent_id,
                    total_count,
                    total_count + word_count,
                ))
                sent_id += 1
                total_count = total_count + word_count
            para_id += 1

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
        c.execute('''PRAGMA page_size = 4096;''')
        c.execute('''VACUUM;''')
        c.execute('''CREATE TABLE corpus (
            corpus_id TEXT,
            title TEXT NOT NULL,
            PRIMARY KEY (corpus_id)
        )''')
        c.execute('''CREATE TABLE book (
            book_id,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
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
        c.execute('''CREATE TABLE sentence (
            chapter_id INT,
            para_id INT,
            sent_id INT,
            offset_start INT NOT NULL,
            offset_end INT NOT NULL,
            FOREIGN KEY(chapter_id) REFERENCES chapter(chapter_id),
            PRIMARY KEY (chapter_id, para_id, sent_id)
        )''')

        chapter_id = 0
        while True:
            try:
                record = self.recStore.fetch_record(self.session, chapter_id)
            except ObjectDoesNotExistException:
                break
            self.rdb_index_record(record)
            yield "Cached %d" % chapter_id
            chapter_id += 1
        yield "Committing..."
        self.rdb.commit()
        yield "Dumping chapter cache..."
        dump_chapter_cache()


def recreate_rdb():
    import argparse

    parser = argparse.ArgumentParser(description='recreate the RDB, chapter cache based on cheshire3 contents')
    args = parser.parse_args()

    if os.path.exists(C3_SQLITE):
        os.remove(C3_SQLITE)
    cdb = ClicDb()
    for o in cdb.recreate_rdb():
        print(o)


def store_documents():
    import argparse

    parser = argparse.ArgumentParser(description='Given a directory of XML files, import into CLiC')
    parser.add_argument('path', nargs='+', help="Directory containing XML files")
    args = parser.parse_args()

    cdb = ClicDb()
    for o in cdb.store_documents(os.path.abspath(args.path[0])):
        print(o)
