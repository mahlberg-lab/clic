"""Concordance endpoint

Searches texts for given phrase(s).

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: subset to search through, one of shortsus/longsus/nonquote/quote/all. Default 'all' (i.e. all text)
- q: 1+ string to search for. If multiple terms are provided, they will be OR'ed together (i.e. we search for either)
- contextsize: Size of context window around search results. Default 0.
- metadata: Optional data to return, see get_book_metadata in clicdb.py for all options

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

Examples:

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
"""
import re
import unidecode

from clic.db.book import get_book_metadata, get_book
from clic.db.corpora import corpora_to_book_ids
from clic.db.lookup import api_subset_lookup, rclass_id_lookup
from clic.errors import UserError
from clic.tokenizer import parse_query

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
    book_cur = cur.connection.cursor()
    book = None

    for likes in like_sets:
        # Choose an "anchor". We search for this first to narrow the possible
        # outputs as much as possible, then consider the types around each.
        anchor_offset = max(enumerate(likes), key=lambda l: len(l[1]))[0]

        query = ""
        params = dict()
        query += """
            SELECT t.book_id
                  , ARRAY_AGG(c.rel_order ORDER BY c.rel_order) rel_order
                  , ARRAY_AGG(c.crange ORDER BY c.rel_order) full_tokens
                  , t.part_of
               FROM token t
               JOIN LATERAL ( -- i.e. for each valid anchor token, get all tokens around it, including context
                    SELECT t2.ordering - t.ordering + %(anchor_offset)s rel_order
                         , t2.ttype, t2.crange, t2.part_of
                      FROM token t2
                     WHERE t2.book_id = t.book_id
                       AND t2.ordering BETWEEN t.ordering - %(anchor_offset)s - %(contextsize)s
                                           AND t.ordering - %(anchor_offset)s + %(total_likes)s + %(contextsize)s
                    ) c ON TRUE
             WHERE t.book_id IN %(book_ids)s
               AND t.part_of ? %(part_of)s
               AND t.ttype LIKE %(anchor_like)s
          GROUP BY t.book_id, t.crange
        """
        params['anchor_offset'] = anchor_offset
        params['anchor_like'] = likes[anchor_offset]
        params['book_ids'] = book_ids
        params['contextsize'] = contextsize
        params['total_likes'] = len(likes)
        params['part_of'] = str(rclass_ids[0])

        if len(likes) > 1:
            # Make sure all likes surrounding the anchor match our conditions
            # TODO: This isn't considering boundaries. -- she sat."\n"On the pavement?"\n"Yes." --> Should we be numbering all regions, and checking it's part of the same one?
            query += "HAVING SUM(CASE\n"
            for i, l in enumerate(likes):
                if i == anchor_offset:
                    continue  # No point re-checking the anchor
                i = str(i)
                query += "WHEN c.rel_order = " + i + " AND c.ttype LIKE %(like_" + i + ")s AND c.part_of ? %(part_of)s THEN 1\n"
                params['like_' + i] = l
            query += "ELSE 0 END) = %(total_likes)s - 1 -- i.e. We have a match for every CASE\n"

        query += """
          ORDER BY t.book_id, t.crange
        """

        cur.execute(query, params)
        for book_id, rel_order, full_tokens, part_of in cur:
            # Extract portion of tokens that are the node
            node_tokens = full_tokens[rel_order.index(0):rel_order.index(0) + len(likes)]
            if not book or book['id'] != book_id:
                book = get_book(book_cur, book_id, content=True)
            yield to_conc(book['content'], full_tokens, node_tokens, contextsize) + [
                [book['name'], node_tokens[0].lower, node_tokens[-1].upper],
                [
                    int(part_of[str(rclass['chapter.text'])]),
                    int(part_of[str(rclass['chapter.paragraph'])]),
                    int(part_of[str(rclass['chapter.sentence'])]),
                ]
            ]

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
        # TODO: Ideally we'd not mangle text, instead return the tokens here
        # TODO: Write tokenisation scheme in JS?
        concs[-1].append(unidecode.unidecode(full_text[t.lower:t.upper]))
        prev_t = t

    # Add array of indicies that are tokens to the end
    for i, c in enumerate(concs):
        c.append(toks[i])
    return [concs[1]] if contextsize == 0 else concs
