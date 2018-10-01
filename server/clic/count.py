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
from clic.db.book import get_book_metadata
from clic.db.corpora import corpora_to_book_ids
from clic.db.lookup import api_subset_lookup


def count(cur, corpora=['dickens'], subset=['all', 'shortsus', 'longsus', 'nonquote', 'quote'], metadata=[]):
    """
    Get word counts for coprora

    - corpora: List of corpora / book names
    - subset: Subset(s) to return counts for
    - metadata, Array of extra metadata to provide with result, some of
      - 'book_titles' (return dict of book IDs to titles at end of result)
    """
    book_ids = tuple(corpora_to_book_ids(cur, corpora))
    api_subset = api_subset_lookup(cur)
    rclass_ids = tuple(api_subset[s] for s in subset)
    cur.execute("""
        SELECT r.book_id
             , r.rclass_id
             , SUM((SELECT COUNT(*) FROM token t WHERE t.book_id = r.book_id AND t.crange <@ r.crange)) word_count
          FROM region r
         WHERE r.book_id IN %(book_ids)s
           AND r.rclass_id IN %(rclass_ids)s
      GROUP BY r.book_id, r.rclass_id
      ORDER BY r.book_id, r.rclass_id
    """, dict(
        book_ids=book_ids,
        rclass_ids=rclass_ids,
    ))

    # Lookup table of subset name to position
    subset_pos = {}
    for i, s in enumerate(subset):
        subset_pos[api_subset[s]] = i

    cur_row = None
    book_ids = set()
    for (book_id, rclass_id, word_count) in cur:
        if not cur_row or cur_row[0] != book_id:
            book_ids.add(book_id)
            if cur_row:
                yield cur_row
            cur_row = [
                book_id,
            ] + [0] * len(subset)
        # Add this subset to the current row rollup
        cur_row[subset_pos[rclass_id] + 1] += word_count
    if cur_row:
        yield cur_row

    footer = get_book_metadata(cur, book_ids, set(metadata))
    if footer:
        yield ('footer', footer)
