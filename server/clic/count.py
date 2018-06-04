"""Word count endpoint

Returns counts of words within subsets

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: Subset(s) to return counts for, one of shortsus/longsus/nonquote/quote/all.
- metadata: Optional data to return, see clicdb:get_book_metadata() for possible values

Parameters should be provided in querystring format, for example::

    ?corpora=dickens&corpora=AgnesG&subset=all&subset=quote

Returns a ``data`` array, one entry per book. The first item is the book ID in question,
the remaining items are the counts in the subsets, the order matching the subset querystring
parameter.

Examples:

/api/count?corpora=AgnesG&subset=all&subset=quote

    {"data":[
        ["AgnesG",68197,21986]
    ], "version":{"corpora":"master:2affe56","clic:import":"1.6:876222b","clic":"1.7beta2:a1f93e7"}}
"""

def word_count(cdb, corpora=['dickens'], subset=['all', 'shortsus', 'longsus', 'nonquote', 'quote'], metadata=[]):
    """
    Get word counts for coprora

    - corpora: List of corpora / book names
    - subset: Subset(s) to return counts for
    - metadata, Array of extra metadata to provide with result, some of
      - 'book_titles' (return dict of book IDs to titles at end of result)
    """
    (where, params) = cdb.corpora_list_to_query(corpora, db='rdb')
    query = " ".join((
        "SELECT c.book_id, s.subset_type",
        ", SUM(s.offset_end - s.offset_start) word_count",
        "FROM subset s, chapter c",
        "WHERE s.chapter_id = c.chapter_id",
        "AND s.offset_end > s.offset_start", # Ignore 0-length subsets
        "AND ", where,
        "AND s.subset_type IN (", ",".join("?" for x in xrange(len(subset))), ")",
        "GROUP BY 1,2",
    ))
    if 'all' in subset:
        # Also fetch entire-chapter counts if required
        query += " ".join((
            " UNION ALL",
            "SELECT c.book_id, 'all' subset_type",
            ", SUM(word_total) word_count",
            "FROM chapter c",
            "WHERE", where,
            "GROUP BY 1,2",
        ))
        params = params + subset + params
    else:
        params.extend(subset)
    query += " ORDER BY 1,2"
    results = cdb.rdb_query(query, params)

    # Lookup table of subset name to position
    subset_pos = {}
    for i, s in enumerate(subset):
        subset_pos[s] = i

    yield {} # Return empty header
    cur_row = None
    book_ids = set()
    for (book_id, subset_type, word_count) in results:
        if not cur_row or cur_row[0] != book_id:
            book_ids.add(book_id)
            if cur_row:
                yield cur_row
            cur_row = [
                book_id,
            ] + [0] * len(subset)
        # Add this subset to the current row rollup
        cur_row[subset_pos[subset_type] + 1] += word_count
    if cur_row:
        yield cur_row

    footer = cdb.get_book_metadata(book_ids, set(metadata))
    if footer:
        yield ('footer', footer)
