"""Concordance endpoint
***********************

Searches texts for given phrase(s).

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: subset to search through, one of shortsus/longsus/nonquote/quote/all. Default 'all' (i.e. all text)
- q: 1+ string to search for. If multiple terms are provided, we will search for each in turn
- contextsize: Size of context window around search results. Default 0.
- metadata: Optional data to return, see `book_metadata.py <db/book_metadata.py>`__ for all options.

Parameters should be provided in querystring format, for example::

    ?corpora=dickens&corpora=AgnesG&q=my+hands&q=my+feet

Returns a ``data`` array, one entry per result. Each item is an array with the following items:

* The left context window (if ``contextsize`` > 0, otherwise omitted)
* The node (i.e. the text searched for)
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

Query (q parameter) format
--------------------------

Queries are broken down using the `tokenizer <../clic.tokenizer>`__ into lists of
types to search for. This means any punctuation, spaces or newlines are
ignored.

Queries can use the wildcard character, ``*``, to search for 0 or more
characters at this point. For example, ``oliver`` will find instances of
"Oliver" and "olvier", but ``oliver*`` will find "Oliver's" in addition. The
asterisk can be used anywhere within a type, not just at the end.

Examples
--------

/api/concordance?corpora=AgnesG&q=his+hands&q=his+feet&contextsize=3::

    {"data":[
      [
        ["to"," ","put"," ","into"," ",[0,2,4]],
        ["his"," ","hands",","," ",[0,2]],
        ["it"," ","should"," ","bring",[0,2,4]],
         . . .
      ], [
        ["the"," ","fire",","," ","with"," ",[0,2,5]],
        ["his"," ","hands"," ",[0,2]],
        ["behind"," ","his"," ","back",[0,2,4]],
         . . .
      ], [
        ["was"," ","frisking"," ","at"," ",[0,2,4]],
        ["his"," ","feet",","," ",[0,2]],
        ["and"," ","finally"," ","upon",[0,2,4]],
         . . .
      ],
    ], "version":{"corpora":"master:fc4de7c", "clic":"1.6:95bf699"}}

Method
------

The concordance search peforms the following steps:

1. Resolve the corpora option to a list of book IDs, translate the subset
   selection to a database region.

2. Tokenise each provided query using the standard method in `tokenizer <../clic.tokenizer>`_,
   converting into a list of database `like expressions`_ for types.
   Note that the CLiC UI generally only provides
   one query, unless you select "Any word", in which case it separates on
   whitespace and gives multiple queries. For example:

   * "He s* her foot" (whole phrase) results in one query ``['he', 's%', 'her', 'foot']``
   * "latter pavement" (any word) results in 2 queries, ``['latter']`` and ``['pavement']``

3. For each query, choose an "anchor" type. The aim here is to find the least
   frequent term that will filter the results the fastest. Currently we choose
   the longest search term. ``["on", "*", "pavement"]`` will use ``pavement``
   as the anchor.

4. Search the database for all types that match this anchor in the given books,
   and within the given region. For example if our query was ``oliver*``, this
   would match the types ``oliver``, ``oliver's``, ``olivers``, etc.

5. For each match, fetch the rest of the node types and context, if required.

6. Check that any remaining types in the node also match the query and are in a
   relevant region.

7. Combine the results with the text from the original book, add the
   chapter/paragraph/sentence statistics from the anchor, return result.

.. _like expressions: https://www.postgresql.org/docs/9.5/static/functions-matching.html#SECT2

Examples / edge cases
---------------------

These are the corpora we use for the following tests::

    >>> db_cur = test_database(
    ... alice='''
    ... ‘Well!’ thought Alice to herself, ‘after such a fall as this, I shall
    ... think nothing of tumbling down stairs! How brave they’ll all think me at
    ... home! Why, I wouldn’t say anything about it, even if I fell off the top
    ... of the house!’ (Which was very likely true.)
    ...
    ... ‘I beg your pardon,’ said Alice very humbly: ‘you had got to the fifth
    ... bend, I think?’
    ...
    ... ‘I had NOT!’ cried the Mouse, sharply and very angrily.
    ... ''',
    ...
    ... willows='''
    ... ‘Get off!’ spluttered the Rat, with his mouth full.
    ...
    ... ‘Thought I should find you here all right,’ said the Otter cheerfully.
    ... ‘They were all in a great state of alarm along River Bank when I arrived
    ... this morning.
    ... ''')

``f*ll *`` matches fall or fell, and selects the word next to it::

    >>> format_conc(concordance(db_cur, ['alice'], q=['f*ll *']))
    [['alice', 49, 'fall', 'as'],
     ['alice', 199, 'fell', 'off']]

We don't match ``cheerfully`` in willows, though::

    >>> format_conc(concordance(db_cur, ['willows'], q=['f*ll *']))
    [['willows', 47, 'full', 'Thought']]

Can use ``?`` to match precisely one character::

    >>> format_conc(concordance(db_cur, ['willows'], q=['the?']))
    [['willows', 126, 'They']]

...where ``*`` matches 0 or many characters::

    >>> format_conc(concordance(db_cur, ['willows'], q=['the*']))
    [['willows', 23, 'the'], ['willows', 103, 'the'], ['willows', 126, 'They']]

Search multiple books at the same time::

    >>> format_conc(concordance(db_cur, ['alice', 'willows'], q=['f*ll *']))
    [['alice', 49, 'fall', 'as'],
     ['alice', 199, 'fell', 'off'],
     ['willows', 47, 'full', 'Thought']]

Multiple queries can be done too (which is ordinarily used for the "Any word"
option). We select the word before fall, and the word after fell::

    >>> format_conc(concordance(db_cur, ['alice'], q=['* fall', 'fell *']))
    [['alice', 47, 'a', 'fall'],
     ['alice', 199, 'fell', 'off']]

Since queries are tokenised first, punctuation / case of queries is ignored.
NB: I is capitalised since we return the token from the text, not the type we
search for::

    >>> format_conc(concordance(db_cur, ['alice'], q=['"i--FELL--off!"']))
    [['alice', 197, 'I', 'fell', 'off']]
    >>> format_conc(concordance(db_cur, ['alice'], q=['i fell off']))
    [['alice', 197, 'I', 'fell', 'off']]

Similarly, apostrophes are normalised (don’t vs don't), so it doesn't matter
which type of apostrophe is searched for (Note the output always matches the
original text)::

    >>> format_conc(concordance(db_cur, ['alice'], q=["wouldn't"], contextsize=[1]))
    [['alice', 157, 'I', '**', 'wouldn’t', '**', 'say']]
    >>> format_conc(concordance(db_cur, ['alice'], q=["wouldn’t"], contextsize=[1]))
    [['alice', 157, 'I', '**', 'wouldn’t', '**', 'say']]

Examples: subset selection
--------------------------

Results can be limited to regions. We can get quote concordances::

    >>> format_conc(concordance(db_cur, ['alice', 'willows'], q=["thought"], subset=["quote"], contextsize=[1]))
    [['willows', 55, 'full', '**', 'Thought', '**', 'I']]

...nonquote concordances::

    >>> format_conc(concordance(db_cur, ['alice', 'willows'], q=["thought"], subset=["nonquote"], contextsize=[1]))
    [['alice', 9, 'Well', '**', 'thought', '**', 'Alice']]

...or all (the default)::

    >>> format_conc(concordance(db_cur, ['alice', 'willows'], q=["thought"], contextsize=[1]))
    [['alice', 9, 'Well', '**', 'thought', '**', 'Alice'],
     ['willows', 55, 'full', '**', 'Thought', '**', 'I']]

When searching in subsets, we do *not* consider boundaries, searching for
"think I" finds a match that straddles 2 quotes::

    >>> format_conc(concordance(db_cur, ['alice', 'willows'], q=["think I"], subset=["quote"], contextsize=[5]))
    [['alice', 341, 'to', 'the', 'fifth', 'bend', 'I',
      '**', 'think', 'I', '**',
      'had', 'NOT', 'cried', 'the', 'Mouse']]

Query parsing
-------------

Query parsing is done by tokenising the string using the `tokenizer module
<../clic.tokenizer/>` into a list of types, see there for more information.

When we parse for concordance search queries, we preserve asterisks and convert
them into percent marks, which is what the database uses to mean "0 or more
characters" in like expressions (see `concordance <concordance.py>`__)::

    >>> parse_query('''
    ... We have *books everywhere*!
    ...
    ... Moo* * oi*-nk
    ... ''')
    ['we', 'have', '%books', 'everywhere%',
     'moo%', '%', 'oi%-nk']

If the same phrase was in a book, we would throw away the asterisks when
converting to types::

    >>> [x[0] for x in types_from_string('''
    ... We have *books everywhere*!
    ...
    ... Moo* * oi*-nk
    ... ''')]
    ['we', 'have', 'books', 'everywhere',
     'moo', 'oi', 'nk']

We also support ``?`` for single characters, which get turned into a like
expression ``_``::

    >>> [x for x in parse_query('''To the ?th degree''')]
    ['to', 'the', '_th', 'degree']

"""
import re

from clic.db.book import get_book
from clic.db.book_metadata import get_book_metadata
from clic.db.corpora import corpora_to_book_ids
from clic.db.lookup import api_subset_lookup, rclass_id_lookup
from clic.errors import UserError
from clic.tokenizer import types_from_string

RE_WHITESPACE = re.compile(r'(\s+)')  # Capture the whitespace so split returns it


def concordance(cur, corpora=['dickens'], subset=['all'], q=[], contextsize=['0'], metadata=[]):
    """
    Main entry function for concordance search

    - corpora: List of corpora / book names
    - subset: Subset to search within, or 'all'
    - q: Quer(ies) to search for, results will contain one of the given expressions
    - contextsize: Size of context window, defaults to none.
    - metadata, Array of extra metadata to provide with result, some of
      - 'book_titles' (return dict of book IDs to titles at end of result)
    """
    book_ids = tuple(corpora_to_book_ids(cur, corpora))
    if len(book_ids) == 0:
        raise UserError("No books to search", "error")
    api_subset = api_subset_lookup(cur)
    rclass = rclass_id_lookup(cur)
    rclass_ids = tuple(api_subset[s] for s in subset)
    if len(rclass_ids) != 1:
        raise UserError("You must supply exactly one subset", "error")
    like_sets = [parse_query(s) for s in q]
    if len(like_sets) == 0:
        raise UserError("You must supply at least one search term", "error")
    contextsize = int(contextsize[0])
    metadata = set(metadata)
    book = None

    book_cur = cur.connection.cursor()
    try:
        for likes in like_sets:
            # Choose an "anchor". We search for this first to narrow the possible
            # outputs as much as possible, then consider the types around each.
            anchor_offset = max(enumerate(likes), key=lambda l: len(l[1]))[0]

            query = ""
            params = dict()
            query += """
                 SELECT t.book_id
                      , c.node_start - 1 node_start -- NB: Postgres is 1-indexed
                      , c.cranges full_tokens
                      , t.part_of
                   FROM token t
                   JOIN LATERAL ( -- i.e. for each valid anchor token, get all tokens around it, including context
                       SELECT ARRAY_POSITION(ARRAY_AGG(t_surrounding.ordering = t.ordering ORDER BY book_id, ordering), TRUE) - %(anchor_offset)s node_start
                            , ARRAY_AGG(CASE WHEN t_surrounding.ordering < (t.ordering - %(anchor_offset)s) THEN t_surrounding.ttype -- i.e. part of the context, so rclass irrelevant
                                             WHEN t_surrounding.ordering > (t.ordering - %(anchor_offset)s + %(total_likes)s - 1) THEN t_surrounding.ttype -- i.e. part of the context, so rclass irrelevant
                                             WHEN t_surrounding.part_of ? %(part_of)s THEN t_surrounding.ttype
                                             ELSE NULL -- part of the node, but not in the right rclass, NULL should fail any node checks later on
                                              END ORDER BY book_id, ordering) ttypes
                            , ARRAY_AGG(t_surrounding.crange ORDER BY book_id, ordering) cranges
                         FROM token t_surrounding
                        WHERE t_surrounding.book_id = t.book_id
                          AND t_surrounding.ordering BETWEEN t.ordering - %(anchor_offset)s - %(contextsize)s
                                             AND t.ordering - %(anchor_offset)s + (%(total_likes)s - 1) + %(contextsize)s
                   ) c on TRUE
                 WHERE t.book_id IN %(book_ids)s
                   AND t.part_of ? %(part_of)s
            """
            params['anchor_offset'] = anchor_offset
            params['anchor_like'] = likes[anchor_offset]
            params['book_ids'] = book_ids
            params['contextsize'] = contextsize
            params['total_likes'] = len(likes)
            params['part_of'] = str(rclass_ids[0])

            for i, l in enumerate(likes):
                if i == anchor_offset:
                    # We should check the main token table for the anchor node, so
                    # postgres searches for this first
                    query += "AND t.ttype LIKE %(like_" + str(i) + ")s\n"
                else:
                    query += "AND c.ttypes[c.node_start + " + str(i) + "] LIKE %(like_" + str(i) + ")s\n"
                params["like_" + str(i)] = l

            cur.execute(query, params)
            for book_id, node_start, full_tokens, part_of in cur:
                # Extract portion of tokens that are the node
                node_tokens = full_tokens[node_start:node_start + len(likes)]
                if not book or book['id'] != book_id:
                    book = get_book(book_cur, book_id, content=True)
                yield to_conc(book['content'], full_tokens, node_tokens, contextsize) + [
                    [book['name'], node_tokens[0].lower, node_tokens[-1].upper],
                    [
                        int(part_of.get(str(rclass['chapter.text']), -1)),
                        int(part_of.get(str(rclass['chapter.paragraph']), -1)),
                        int(part_of.get(str(rclass['chapter.sentence']), -1)),
                    ]
                ]
    finally:
        book_cur.close()

    footer = get_book_metadata(cur, book_ids, metadata)
    if footer:
        yield ('footer', footer)


def to_conc(full_text, full_tokens, node_tokens, contextsize):
    """
    Convert full text + tokens back into wire format
    - full_text: String covering entire area, including window
    - full_tokens: List of tokens, including window
    - node_tokens: List of tokens, excluding window
    - contextsize: Number of tokens should be in window, if 0 then don't return window

    A token is a NumericRange type indicating the range in full_text it corresponds to
    """
    concs = [[]]
    toks = [[]]

    def append_if_nonempty(l, s):
        if s:
            l.append(s)

    prev_t = None
    for t in full_tokens:
        # Non-word characters before this word
        intra_word = full_text[prev_t.upper:t.lower] if prev_t else ''
        if t == node_tokens[0]:
            # First token of node
            concs.append([])
            toks.append([])
            intra_word = re.split(RE_WHITESPACE, intra_word, maxsplit=1)
            append_if_nonempty(concs[-2], intra_word[0])
            if len(intra_word) > 1:
                append_if_nonempty(concs[-2], intra_word[1])  # NB: Window gets space, not node
                append_if_nonempty(concs[-1], intra_word[2])
        elif prev_t == node_tokens[-1]:
            # First token of right-window
            concs.append([])
            toks.append([])
            intra_word = re.split(RE_WHITESPACE, intra_word, maxsplit=1)
            append_if_nonempty(concs[-2], intra_word[0])
            if len(intra_word) > 1:
                append_if_nonempty(concs[-1], intra_word[1])  # NB: Window gets space, not node
                append_if_nonempty(concs[-1], intra_word[2])
        else:
            # Add non-word characters before current tokens
            append_if_nonempty(concs[-1], intra_word)
        # Add word token
        toks[-1].append(len(concs[-1]))
        concs[-1].append(full_text[t.lower:t.upper])
        prev_t = t

    # Add array of indicies that are tokens to the end
    for i, c in enumerate(concs):
        c.append(toks[i])
    if len(concs) < 3:
        concs.append([[]])
    return [concs[1]] if contextsize == 0 else concs


def parse_query(q):
    """
    Turn a query string into a list of LIKE expressions
    """
    def term_to_like(t):
        """Escape any literal LIKE terms, convert * to %"""
        return (t.replace('\\', '\\\\')
                 .replace('%', '\\%')
                 .replace('_', '\\_')
                 .replace('?', '_')
                 .replace('*', '%'))

    return list(term_to_like(t) for t, word_start, word_end in types_from_string(q, additional_word_parts=set((
        '*',  # Consider * to be part of a type, 0-or-more chars
        '?',  # Consider * to be part of a type, exactly 1 char
    ))))
