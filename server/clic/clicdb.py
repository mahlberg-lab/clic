# -*- coding: utf-8 -*-
import array
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

from clic.c3chapter import Chapter
from clic.errors import UserError


class ClicDb():
    def __init__(self, rdb_file=C3_SQLITE):
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

        self.rdb = sqlite3.connect(rdb_file)
        self.rdb.execute('PRAGMA mmap_size = %d;' % (1024**3))
        self.rdb.execute("PRAGMA foreign_keys = ON;")
        self.rdb.execute("PRAGMA page_size = 4096;")

    def close(self):
        self.rdb.close()

    def warm_cache(self):
        """
        Any warm operations we may have in the future
        """
        pass

    def corpora_list_to_query(self, corpora, db='cheshire'):
        """
        Given a list of books / entire subcorpora, return a query clause
        - db == 'cheshire': Return a CQL where clause string
        - db == 'rdb': Return (SQL where clause, params)
        """
        corpus_names = dict((x[0], True) for x in self.rdb_query("SELECT corpus_id FROM corpus"))
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

    def get_clic_version(self):
        """
        Get current version of CLiC code & corpora
        """
        out = {}

        # Fetch versions from DB
        for (repo, version) in self.rdb_query("SELECT repository_id, version FROM repository"):
            out[repo] = version

        # CLiC might have been upgraded since import
        with open(os.path.join(CLIC_DIR, '..', 'clic_revision')) as f:
            out['clic'] = f.read().strip()

        return out

    def get_book_metadata(self, book_ids, metadata):
        """
        Generate dict of metadata that should go in footer of both concordance and subsets
        - book_ids: Array of book IDs to include
        - metadata: Metadata items to include, a set contining some of...
          - 'book_titles': The title / author of each book
          - 'chapter_start': The start word ID for all achpters (i.e. the length of the previous)
        """
        out = {}
        def p_params(*args):
            return ("?, " * sum(len(x) for x in args)).rstrip(', ')

        if 'book_titles' in metadata:
            out['book_titles'] = {}
            for (book_id, title, author) in self.rdb_query(
                    "SELECT book_id, title, author FROM book" +
                    " WHERE book_id IN (" + p_params(book_ids) + ")",
                    tuple(book_ids)):
                out['book_titles'][book_id] = (title, author)

        if 'chapter_start' in metadata:
            out['chapter_start'] = {}
            for (book_id, chapter_num, word_total) in self.rdb_query(
                    "SELECT book_id, chapter_num, word_total FROM chapter" +
                    " WHERE book_id IN (" + p_params(book_ids) + ")" +
                    " ORDER BY 1, 2",
                    tuple(book_ids)):
                if book_id not in out['chapter_start']:
                    out['chapter_start'][book_id] = dict(_end=0)
                out['chapter_start'][book_id][chapter_num] = out['chapter_start'][book_id]['_end']
                out['chapter_start'][book_id]['_end'] += word_total

        return out

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
        return (book_id, chapter_num, count_prev_chap, total_word)

    def get_chapter(self, chapter_id):
        old_text_factory = self.rdb.text_factory
        self.rdb.text_factory = str
        (tokens, word_map) = self.rdb_query("SELECT tokens, word_map FROM tokens WHERE chapter_id = ? ", (chapter_id,)).fetchone()
        self.rdb.text_factory = old_text_factory

        tokens = tuple(tokens.decode('utf8').split(b'\x00'))
        word_map = array.array('L', word_map)
        return Chapter(tokens, word_map)

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
        index = self.db.get_object(self.session, index_name)
        try:
            return index.facets(self.session, results)
        finally:
            # NB: Tidy up after index.py, facets calls fetch_termById which opens
            # termId/vector/proxVector BDB connections but never closes.
            index.indexStore._closeVectors(index.indexStore.session, index)

    def get_word(self, chapter_id, match):
        """
        Given a chapter_id and CLiC proxInfo match, return an array of:
        - word_id: word position in chapter
        - para_chap: word's paragraph position in chapter
        - sent_chap: word's sentence position in chapter

        The match should be from result.proxInfo, an array of at least:
        - eid (i.e. the start node index)
        - word_offset (i.e. eid offset in chapter + word_offset = word offset in chapter)
        The following may also exist, but are ignored:
        - o (i.e. the o(ffset) attribute on the node word in question)
        - Count of words in chapter(?)
        """
        eid, word_id = match[0:2]
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
        qf = self.db.get_object(self.session, 'defaultQueryFactory')

        try:
            return self.db.search(self.session, qf.get_query(self.session, query))
        finally:
            # Tidy up after index.py, which doesn't close it's indexStores when
            # it's done with them.
            # In index.py, store.fetch_termList opens a connection to the index
            # BDB files, but nothing closes them afterwards.
            # Find the indexes that are currently open and close them all manually
            idxStore = self.db.get_object(self.session, 'indexStore')
            for i in idxStore.indexCxn.keys():
                idxStore._closeIndex(idxStore.session, i)

        return results

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

        yield "Loading XML files..."
        df.load(self.session, doc_dir)  # Pulls out <div> sections of every document,
        recStore.begin_storing(self.session)
        db.begin_indexing(self.session)
        for d in df:
            rec2 = None
            try:
                doc = ampPreP.process_document(self.session, d)  # Escapes ampersands
                rec = xmlp.process_document(self.session, doc)  # LXML parser
                genia = geniaTxr.process_record(self.session, rec) # corpusTransformer (SimpleExtractor - Mark up words / whitepace)
                rec2 = xmlp.process_document(self.session, genia)  # LXML parser
                recStore.create_record(self.session, rec2)  # Assign ID to record. store in recordStore BDB
                db.add_record(self.session, rec2)  # Register document with DB
                indexWF.process(self.session, rec2)  # Apply indexing to record

                # Index new record in RDB
                self.rdb_index_record(recStore.fetch_record(self.session, rec2.id))
                yield "Indexed %d - %s" % (rec2.id, d.filename)
            except Exception as e:
                import traceback

                yield "Failed to index %s:-\n%s" % (
                    d.filename,
                    traceback.format_exc(),
                )
                raise e
        yield "Committing..."
        recStore.commit_storing(self.session)  # NB: This will release .bdb file handles
        db.commit_indexing(self.session)
        self.rdb.commit()
        self.rdb.execute("VACUUM;")

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

        # Extra lookup tables not available from cheshire data
        if not hasattr(self, 'extra_data'):
            with open(os.path.join(CLIC_DIR, '..', 'annotationOutput', 'extra_data.json')) as f:
                self.extra_data = json.load(f)

            # Update the repository versions in the DB
            for repo, version in self.extra_data["repository_versions"].items():
                c.execute('DELETE FROM repository WHERE repository_id = ?', (repo,))
                _rdb_insert(c, "repository", (repo, version))

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
            self.extra_data['corpus_order'].get(corpus_id, 999),
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
        subset_nodes = dom.xpath('|'.join('//%s[@eid]' % t for t in ["qs", "qe", "sls", "sle", "sss", "sse"]))
        subset_nodes.sort(key=lambda n: int(n.attrib['eid']))
        for n in subset_nodes:
            node[n.tag] = n
            if 'wordOffset' not in n.attrib:
                # NB: The top/tail qs/qe markings don't have wordOffset on older c3 entries,
                # assume it's either the first or the last node
                n.attrib['wordOffset'] = u'0' if n == subset_nodes[0] else unicode(word_count)

            if n.tag in ['qs']:
                # Start of a quote, thus up to the last qe is a non-quote
                start_node = node.get('qe', None)
            elif n.tag.endswith('e'):
                # End of a subset
                start_node = node.get(n.tag[0:-1] + 's', None)
            else:
                # Not the end of a subset, move on
                continue

            offset_start = int(0 if start_node is None else start_node.attrib['wordOffset'])
            offset_end = int(n.attrib['wordOffset'])
            if offset_start == offset_end:
                # No point storing 0-length subsets
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
                offset_start,
                offset_end,
            ))

        if 'qe' in node:
            # End of quote up until end of text is non-quote
            _rdb_insert(c, "subset", (
                chapter_id,
                node['qe'].attrib['eid'],
                'nonquote',
                node['qe'].attrib['wordOffset'],
                word_count,
            ))

        # Index lengths of all paragraphs/sentences
        total_count = 0
        for para_node in dom.xpath("/div/p"):
            for sentence_node in para_node.xpath("s"):
                word_count = int(sentence_node.xpath("count(descendant::w)"))
                _rdb_insert(c, "sentence", (
                    chapter_id,
                    int(para_node.attrib['pid']),
                    int(sentence_node.attrib['sid']),
                    total_count,
                    total_count + word_count - 1,
                ))
                total_count = total_count + word_count

        # Token indexing
        toks = dom.xpath("/div/descendant::*[self::n or self::w]")
        _rdb_insert(c, "tokens", (
            chapter_id,
            b'\x00'.join(n.text.encode('utf8') for n in toks),
            array.array('L', (i for i, n in enumerate(toks) if n.tag == 'w')).tostring(),
        ))

    def create_schema(self):
        c = self.rdb.cursor()
        c.execute('''CREATE TABLE repository (
            repository_id TEXT,
            version TEXT NOT NULL,
            PRIMARY KEY (repository_id)
        )''')
        c.execute('''CREATE TABLE corpus (
            corpus_id TEXT,
            title TEXT NOT NULL,
            ordering INT,
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
        c.execute('''CREATE TABLE tokens (
            chapter_id INT,
            tokens BLOB,
            word_map BLOB,
            FOREIGN KEY(chapter_id) REFERENCES chapter(chapter_id),
            PRIMARY KEY (chapter_id)
        )''')

    def recreate_rdb(self):
        recStore = self.db.get_object(self.session, 'recordStore')

        self.create_schema()
        chapter_id = 0
        while True:
            try:
                record = recStore.fetch_record(self.session, chapter_id)
            except ObjectDoesNotExistException:
                break
            self.rdb_index_record(record)
            yield "Cached %d" % chapter_id
            chapter_id += 1
        yield "Committing..."
        self.rdb.commit()
        self.rdb.execute("VACUUM;")
        # Force recordStore to release .bdb file handles
        recStore._closeAll(recStore.session)


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
