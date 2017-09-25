# -*- coding: utf-8 -*-
def subset(cdb, corpora=['dickens'], subset=['quote'], contextsize=['0']):
    """
    - corpora: List of corpora / book names
    - subset: Subset(s) to search for.
    """
    contextsize = int(contextsize[0])

    (where, params) = cdb.corpora_list_to_query(corpora, db='rdb')
    query = " ".join((
        "SELECT s.chapter_id, s.offset_start, s.offset_end",
        "FROM subset s, chapter c",
        "WHERE s.chapter_id = c.chapter_id",
        "AND ", where,
        "AND s.subset_type IN (", ",".join("?" for x in xrange(len(subset))), ")",
    ))
    params.extend(subset)

    yield {} # Return empty header
    cur_chapter = None
    for (chapter_id, offset_start, offset_end) in cdb.rdb_query(query, params):
        if not cur_chapter or cur_chapter != chapter_id:
            cur_chapter = chapter_id
            ch = cdb.get_chapter(cur_chapter)
            (count_prev_chap, total_word) = cdb.get_chapter_word_counts(ch.book, int(ch.chapter))

        yield ch.get_conc_line(offset_start, offset_end - offset_start, contextsize) + [
                [ch.book, ch.chapter, 0, 0], # TODO: Paragraph / sentence counts
                [count_prev_chap + int(offset_start), total_word, chapter_id, offset_start, offset_end],
        ]
