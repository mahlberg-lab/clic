# -*- coding: utf-8 -*-
"""Subset endpoint

Returns subsets of given texts, for example quotations.

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: subset to return, one of shortsus/longsus/nonquote/quote/all. Default 'all' (i.e. all text)
- contextsize: Size of context window around subset. Default 0.
- metadata: Optional data to return, see `book_metadata.py <db/book_metadata.py>`__ for all options.

Parameters should be provided in querystring format, for example::

    ?corpora=dickens&corpora=AgnesG&subset=quote

Returns a ``data`` array, one entry per result. The data array is sorted by the book id,
then chapter number. Each item is an array with the following items:

* The left context window (if ``contextsize`` > 0, otherwise omitted)
* The node (i.e. the subset)
* The right context window (if ``contextsize`` > 0, otherwise omitted)
* Result metadata
* Position-in-book metadata

Each of left/node/right context window is an array of word/non-word tokens, with the final item
indicating which of the tokens are word tokens. For example::

    [
        'while',
        ' ',
        'this',
        ' ',
        'shower',
        ' ',
        'gets',
        ' ',
        'owered',
        ",'",
        ' ',
        [0, 2, 4, 6, 8],
    ]

Result metadata and Position-in-book metadata are currently subject to change.

The ``version`` object gives both the current version of CLiC and the revision of the
corpora ingested in the database.

Examples:

/api/subset?corpora=AgnesG&subset=longsus::

    {"data":[
      [["observed"," ","Smith",";"," ","'","and"," ","a"," ","darksome"," ",[0,2,6,8,10]], . . .],
      [["replied"," ","she",","," ","with"," ","a"," ","short",","," ","bitter"," ","laugh",";"," ",[0,2,5,7,9,12,14]], . . .],
       . . .
    ], "version":{"corpora":"master:fc4de7c", "clic":"1.6:95bf699"}}

/api/subset?corpora=AgnesG&subset=longsus&contextsize=3::

    {"data":[
      [
        ["you",","," ","Miss"," ","Agnes",",'"," ",[0,3,5]],
        ["observed"," ","Smith",";"," ","'","and"," ","a"," ","darksome"," ",[0,2,6,8,10]],
        ["'","un"," ","too",";"," ","but",[1,3,6]],
         . . .
      ], [
        ["shown"," ","much"," ","mercy",",'"," ",[0,2,4]],
        ["replied"," ","she",","," ","with"," ","a"," ","short",","," ","bitter"," ","laugh",";"," ",[0,2,5,7,9,12,14]],
        ["'","killing"," ","the"," ","poor",[1,3,5]],
         . . .
      ],
    ], "version":{"corpora":"master:fc4de7c", "clic":"1.6:95bf699"}}

Method
------

The subset search peforms the following steps:
1. Resolve the corpora option to a list of book IDs, translate the subset
   selection to a database region.

2. For each region, find all tokens within the region, and (contextsize) + 10 characters
   either side (it is faster to approximate the context's number of characters
   than get (contextsize) words).

3. Combine the results with the text from the original book, add the
   chapter/paragraph/sentence statistics for the first node in the region, return result.

Examples / edge cases
---------------------

    >>> db_cur = test_database(
    ... alice='''
    ... ‘Well!’ thought Alice to herself, ‘after such a fall as this, I shall
    ... think nothing of tumbling down stairs! How brave they’ll all think me at
    ... home! Why, I wouldn’t say anything about it, even if I fell off the top
    ... of the house!’ (Which was very likely true.)
    ... ''',
    ...
    ... willows='''
    ... ‘Get off!’ spluttered the Rat, with his mouth full.
    ...
    ... ‘Thought I should find you here all right,’ said the Otter cheerfully.
    ... ‘They were all in a great state of alarm along River Bank when I arrived
    ... this morning.’
    ... ''')

We can ask for quotes::

    >>> format_conc(subset(db_cur, ['alice', 'willows'], subset=['quote']))
    [['alice', 1, 'Well'],
     ['alice', 35, 'after', 'such', 'a', 'fall', 'as', 'this', 'I', 'shall',
     'think', 'nothing', 'of', 'tumbling', 'down', 'stairs', 'How', 'brave',
     'they’ll', 'all', 'think', 'me', 'at', 'home', 'Why', 'I', 'wouldn’t',
     'say', 'anything', 'about', 'it', 'even', 'if', 'I', 'fell', 'off', 'the',
     'top', 'of', 'the', 'house'],
     ['willows', 1, 'Get', 'off'],
     ['willows', 54, 'Thought', 'I', 'should', 'find', 'you', 'here', 'all', 'right'],
     ['willows', 125, 'They', 'were', 'all', 'in', 'a', 'great', 'state', 'of',
      'alarm', 'along', 'River', 'Bank', 'when', 'I', 'arrived', 'this', 'morning']]

Or nonquotes, from a single book::

    >>> format_conc(subset(db_cur, ['alice'], subset=['nonquote']))
    [['alice', 9, 'thought', 'Alice', 'to', 'herself'],
     ['alice', 231, 'Which', 'was', 'very', 'likely', 'true']]

Context size can also be configured, but the return is only approximate::

    >>> format_conc(subset(db_cur, ['alice'], subset=['nonquote'], contextsize=[3]))
    [['alice', 9, 'Well', '**', 'thought', 'Alice', 'to', 'herself', '**', 'after', 'such', 'a', 'fall', 'as', 'this', 'I'],
     ['alice', 231, 'off', 'the', 'top', 'of', 'the', 'house', '**', 'Which', 'was', 'very', 'likely', 'true', '**']]

"""
from clic.concordance import to_conc

from clic.db.book import get_book
from clic.db.book_metadata import get_book_metadata
from clic.db.corpora import corpora_to_book_ids
from clic.db.lookup import api_subset_lookup, rclass_id_lookup
from clic.errors import UserError


def subset(cur, corpora=['dickens'], subset=['all'], contextsize=['0'], metadata=[]):
    """
    Main entry function for subset search

    - corpora: List of corpora / book names
    - subset: Subset(s) to search for.
    - contextsize: Size of context window, defaults to none.
    - metadata, Array of extra metadata to provide with result, some of
      - 'book_titles' (return dict of book IDs to titles at end of result)
    """
    book_ids = corpora_to_book_ids(cur, corpora)
    if len(book_ids) == 0:
        raise UserError("No books to search", "error")
    contextsize = int(contextsize[0])
    metadata = set(metadata)
    book_cur = cur.connection.cursor()
    book = None
    api_subset = api_subset_lookup(cur)
    rclass_ids = tuple(api_subset[s] for s in subset)
    rclass = rclass_id_lookup(cur)

    query = """
        SELECT r.book_id
             , ARRAY(SELECT tokens_in_crange(r.book_id, range_expand(r.crange, %(contextsize)s))) full_tokens
             , ARRAY_AGG(t.crange ORDER BY t.book_id, LOWER(t.crange)) node_tokens
             , r.crange node_crange
             , (ARRAY_AGG(t.part_of))[1] part_of
          FROM region r, token t
         WHERE t.book_id = r.book_id AND t.crange <@ r.crange
           AND r.book_id IN %(book_id)s
           AND r.rclass_id IN %(rclass_ids)s
      GROUP BY r.book_id, r.crange -- NB: Not using LOWER(r.crange) (generally faster) means we don't have to scan the table
    """
    params = dict(
        book_id=tuple(book_ids),
        contextsize=contextsize * 10,  # TODO: Bodge word -> char
        rclass_ids=rclass_ids,
    )
    cur.execute(query, params)

    for book_id, full_tokens, node_tokens, node_crange, part_of in cur:
        if not book or book['id'] != book_id:
            book = get_book(book_cur, book_id, content=True)
        yield to_conc(book['content'], full_tokens, node_tokens, contextsize) + [
            [book['name'], node_crange.lower, node_crange.upper],
            [
                int(part_of.get(str(rclass['chapter.text']), -1)),
                int(part_of.get(str(rclass['chapter.paragraph']), -1)),
                int(part_of.get(str(rclass['chapter.sentence']), -1)),
            ]
        ]

    book_cur.close()

    footer = get_book_metadata(cur, book_ids, metadata)
    if footer:
        yield ('footer', footer)
