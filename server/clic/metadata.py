def get_corpus_structure(cdb):
    """
    Return a list of dicts containing:
    - id: corpus short name
    - title: corpus title
    - children: [{id: book id, title: book title, author: book author}, ...]
    """
    c = cdb.rdb_query(
        "SELECT c.corpus_id, c.title, b.book_id, b.title, b.author" +
        " FROM corpus c, book b" +
        " WHERE b.corpus_id = c.corpus_id" +
        " ORDER BY c.ordering, b.title")

    out = []
    for (c_id, c_title, b_id, b_title, b_author) in c:
        if len(out) == 0 or out[-1]['id'] != c_id:
            out.append(dict(id=c_id, title=c_title, children=[]))
        out[-1]['children'].append(dict(id=b_id, title=b_title, author=b_author))
    return out

def get_corpus_details(cdb):
    """
    - Words in entire book, quotes/non-quotes/suspensions
    - links to chapters
    """
    # Get lengths of all subsets
    subset_info = {}
    for (ch_id, s_type, s_length) in cdb.rdb_query(
            "SELECT s.chapter_id, s.subset_type" +
            ", SUM(s.offset_end - s.offset_start) subset_length" +
            " FROM subset s" +
            " GROUP BY 1, 2"):
        if ch_id not in subset_info:
            subset_info[ch_id] = {}
        subset_info[ch_id][s_type] = s_length

    c = cdb.rdb_query(
        "SELECT c.corpus_id, c.title" +
        ", b.book_id, b.title, b.author" +
        ", ch.chapter_id, ch.chapter_num, ch.word_total" +
        " FROM corpus c, book b, chapter ch" +
        " WHERE b.corpus_id = c.corpus_id AND ch.book_id = b.book_id" +
        " ORDER BY c.ordering, b.title, ch.chapter_num")

    out = []
    for (c_id, c_title, b_id, b_title, b_author, ch_id, ch_chapter_num, ch_word_total) in c:
        # If we haven't added the current corpora, insert new record
        if len(out) == 0 or out[-1]['id'] != c_id:
            out.append(dict(id=c_id, title=c_title, subset_info={}, children=[]))

        # If we haven't added the current book, insert new record
        if len(out[-1]['children']) == 0 or out[-1]['children'][-1]['id'] != b_id:
            out[-1]['children'].append(dict(id=b_id, title=b_title, author=b_author, subset_info={}, children=[]))

        ch_subsets = subset_info.get(ch_id, {})
        ch_subsets['all'] = ch_word_total
        # Insert current chapter of current book
        out[-1]['children'][-1]['children'].append(dict(
            id=ch_id,
            chapter_num = ch_chapter_num,
            title = "Chapter %d" % ch_chapter_num,  # TODO: We should have parsed the chapter title
            subset_info = ch_subsets,
        ))

        for (k, v) in ch_subsets.items():
            # Add to book totals
            if k not in out[-1]['children'][-1]['subset_info']:
                out[-1]['children'][-1]['subset_info'][k] = 0
            out[-1]['children'][-1]['subset_info'][k] += v
            # Add to corpus totals
            if k not in out[-1]['subset_info']:
                out[-1]['subset_info'][k] = 0
            out[-1]['subset_info'][k] += v
    return out
