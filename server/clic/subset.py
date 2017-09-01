# -*- coding: utf-8 -*-
def subset(cdb, corpora=['dickens'], subset=['quote']):
    """
    - corpora: List of corpora / book names
    - subset: Subset(s) to search for.
    """
    # Split materials into corpus names and book names
    cnames = cdb.get_corpus_names() 
    corpus, books = [], []
    for m in corpora:
        if m in cnames:
            corpus.append(m)
        else:
            books.append(m)

    query = " ".join((
        "SELECT s.chapter_id, s.offset_start, s.offset_end",
        "FROM subset s, chapter c",
        "WHERE s.chapter_id = c.chapter_id",
        "AND s.subset_type IN (", ",".join("?" for x in xrange(len(subset))), ")",
        "AND (",
            "c.book_id IN (SELECT book_id FROM book WHERE corpus_id IN (", ",".join("?" for x in xrange(len(corpus))), "))",
            "OR",
            "c.book_id IN (", ",".join("?" for x in xrange(len(books))), ")"
        ")",
    ))
    params = subset + corpus + books

    cur_chapter = None
    for (chapter_id, offset_start, offset_end) in cdb.rdb_query(query, params):
        if not cur_chapter or cur_chapter != chapter_id:
            cur_chapter = chapter_id
            ch = cdb.get_chapter(cur_chapter)
            (count_prev_chap, total_word) = cdb.get_chapter_word_counts(ch.book, ch.chapter)

        yield ch.get_conc_line(offset_start, offset_end - offset_start, 3) + [
                [ch.book, ch.chapter, 0, 0], # TODO: Paragraph / sentence counts
                [count_prev_chap + int(offset_start), total_word],
        ]
