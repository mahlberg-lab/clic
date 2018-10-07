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
import unidecode

from clic.db.book import get_book_metadata, get_book
from clic.db.corpora import corpora_to_book_ids
from clic.db.lookup import api_subset_lookup, rclass_id_lookup
from clic.errors import UserError
from clic.tokenizer import parse_query


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
    rclass_ids = tuple(api_subset[s] for s in subset if s != 'all')
    like_sets = [parse_query(s) for s in q]
    if len(like_sets) == 0:
        raise UserError("You must supply at least one search term", "error")
    contextsize = contextsize[0]
    metadata = set(metadata)
    book_cur = cur.connection.cursor()
    book = None

    for likes in like_sets:
        query = """
            SELECT book_id
                 , ARRAY(SELECT tokens_in_crange(book_id, range_expand(RANGE_MERGE(crange), %s))) full_tokens
                 , ARRAY_AGG(crange ORDER BY book_id, LOWER(crange)) node_tokens
                 , RANGE_MERGE(crange) node_range
                 , JSONB_AGG(part_of) part_of
              FROM (
        """
        params = [int(contextsize) * 10]  # TODO: Bodge word -> char

        for i, like in enumerate(likes):
            if i > 0:
                query += "UNION ALL\n"
            query += """
                SELECT t.book_id
                     , t.crange
                     , t.ttype
                     , t.ordering - %s conc_group
                     , tm.part_of
                  FROM token t, token_metadata tm
                 WHERE t.book_id = tm.book_id AND LOWER(t.crange) = tm.lower_crange
                   AND t.book_id IN %s
                   AND t.ttype LIKE %s
            """
            params.extend([i, book_ids, like])
            if len(rclass_ids) > 0:
                # Make sure these tokens are in an appropriate region
                query += " AND tm.part_of ? %s"
                params.extend([str(rclass_ids[0])])
            if len(rclass_ids) > 1:
                raise NotImplementedError()
        query += """
            ) c
            GROUP BY book_id, conc_group
            HAVING COUNT(*) = %s
            ORDER BY book_id, conc_group
        """
        params.append(len(likes))

        cur.execute(query, params)
        for book_id, full_tokens, node_tokens, node_crange, part_of in cur:
            part_of = part_of[0]  # Unwind redundant aggregation
            if not book or book['id'] != book_id:
                book = get_book(book_cur, book_id, content=True)
            conc_left, conc_node, conc_right = to_conc(book['content'], full_tokens, node_tokens)
            yield [
                conc_left,
                conc_node,
                conc_right,
                [book['name'], node_crange.lower, node_crange.upper],
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


def to_conc(full_text, full_tokens, node_tokens):
    """
    Convert full text + tokens back into wire format
    - full_text: String covering entire area, including window
    - full_tokens: List of tokens, including window
    - node_tokens: List of tokens, excluding window

    A token is a NumericRange type indicating the range in full_text it corresponds to
    """
    concs = [[]]
    toks = [[]]

    prev_t = None
    for t in full_tokens:
        if t == node_tokens[0]:
            # TODO: Split non-word characters on space, appending to previous entry (clic/c3chapter.py)
            concs.append([])
            toks.append([])
        if prev_t:
            # Add non-word characters before current tokens
            concs[-1].append(full_text[prev_t.upper:t.lower])
        # Add word token
        toks[-1].append(len(concs[-1]))
        # TODO: Ideally we'd not mangle text, instead return the tokens here
        # TODO: Write tokenisation scheme in JS?
        concs[-1].append(unidecode.unidecode(full_text[t.lower:t.upper]))
        prev_t = t

        if t == node_tokens[-1]:
            # Anything after this is right-hand context
            concs.append([])
            toks.append([])

    # Add array of indicies that are tokens to the end
    for i, c in enumerate(concs):
        c.append(toks[i])
    return concs
