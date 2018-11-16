"""Word count endpoint
**********************

Returns counts of words within subsets

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: Subset(s) to return counts for, one of shortsus/longsus/nonquote/quote/all.
- metadata: Optional data to return, see `book_metadata.py <db/book_metadata.py>`__ for all options.

Parameters should be provided in querystring format, for example::

    ?corpora=dickens&corpora=AgnesG&subset=all&subset=quote

Returns a ``data`` array, one entry per book. The first item is the book ID in question,
the remaining items are the counts in the subsets, the order matching the subset querystring
parameter.

Examples:

``/api/count?corpora=AgnesG&subset=all&subset=quote``::

    {"data":[
        ["AgnesG",68197,21986]
    ], "version":{"corpora":"master:2affe56","clic:import":"1.6:876222b","clic":"1.7beta2:a1f93e7"}}

Method
------

Word count peforms the following steps:

1. Resolve the corpora option to a list of book IDs, translate the subset
   selection to a database region.

2. For each book, count the tokens that appear in each of the selected regions.

Examples / edge cases
---------------------

These are the corpora we use for the following tests::

    >>> db_cur = test_database(
    ... alice='''
    ... Alice's Adventures in Wonderland
    ... Lewis Carroll
    ...
    ... ‘Well!’ thought Alice to herself, ‘after such a fall as this, I shall
    ... think nothing of tumbling down stairs! How brave they’ll all think me at
    ... home! Why, I wouldn’t say anything about it, even if I fell off the top
    ... of the house!’ (Which was very likely true.)
    ... '''.strip(),
    ...
    ... willows='''
    ... The Wind in the Willows
    ... Kenneth Grahame
    ...
    ... ‘Get off!’ spluttered the Rat, with his mouth full.
    ...
    ... ‘Thought I should find you here all right,’ said the Otter cheerfully.
    ... ‘They were all in a great state of alarm along River Bank when I arrived
    ... this morning.
    ... '''.strip())

Get word counts::

    >>> sorted(list(count(db_cur, ['alice', 'willows'], ['all'])))
    [('alice', 49), ('willows', 38)]

Get word counts / word counts both overall and in quotes::

    >>> sorted(list(count(db_cur, ['alice', 'willows'], ['all', 'quote'])))
    [('alice', 49, 40), ('willows', 38, 10)]
"""
from clic.db.book_metadata import get_book_metadata
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
    query = """
        SELECT (SELECT name FROM book WHERE book_id = t.book_id) AS "name"
    """
    params = dict(book_ids=book_ids)
    for r in rclass_ids:
        query += """
             , COUNT(CASE WHEN t.part_of ? '%d' THEN 1 END) is_%d
        """ % (r, r)
    query += """
          FROM token t
         WHERE t.book_id IN %(book_ids)s
      GROUP BY book_id
    """
    cur.execute(query, params)

    for row in cur:
        yield row

    footer = get_book_metadata(cur, book_ids, set(metadata))
    if footer:
        yield ('footer', footer)
