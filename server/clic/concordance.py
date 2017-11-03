# -*- coding: utf-8 -*-
import os
import os.path

from unidecode import unidecode

from clic.errors import UserError
"""Concordance endpoint

Searches texts for given phrase(s).

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: subset to search through, one of shortsus/longsus/nonquote/quote/all. Default 'all' (i.e. all text)
- q: 1+ string to search for. If multiple terms are provided, they will be OR'ed together (i.e. we search for either)
- contextsize: Size of context window around search results. Default 0.

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
    ]}
"""
def concordance(cdb, corpora=['dickens'], subset=['all'], q=[], contextsize=['0']):
    """
    Main entry function for concordance search

    - corpora: List of corpora / book names
    - subset: Subset to search within, or 'all'
    - q: Quer(ies) to search for, results will contain one of the given expressions
    - contextsize: Size of context window, defaults to none.
    """
    idx = cdb.get_subset_index(subset[0])
    contextsize = int(contextsize[0])

    query = build_query(cdb, q, idx, corpora)
    result_set = cdb.c3_query(query)

    return create_concordance(cdb, q, result_set, contextsize)


def build_query(cdb, q, idxName, corpora):
    '''
    Builds a cheshire query
     - q: Quer(ies) to search for
     - idxName: Index to use, e.g. "chapter-idx"
     - corpora: List of subcorpi to search, e.g. ["dickens"]

    Return a CQL query
    '''
    ## define search term
    if len(q) == 0:
        raise UserError("You must supply at least one search term", "error")

    term_clauses = []
    for term in q:
        term_clauses.append(u'c3.{0} = "{1}"'.format(idxName, unicode(unidecode(term))))

    ## conduct database search
    ## note: /proxInfo needed to search individual books
    query = u'(%s) and/proxInfo (%s)' % (
        cdb.corpora_list_to_query(corpora),
        u' or/proxInfo '.join(term_clauses),
    )

    return query


def create_concordance(cdb, q, result_set, contextsize):
    """
    main concordance method
    create a list of lists containing each three contexts left - node -right,
    and a list within those contexts containing each word.
    Add two separate lists containing metadata information:
    [
    [left context - word 1, word 2, etc.],
    [node - word 1, word 2, etc],
    [right context - word 1, etc],
    [chapter metadata],
    [book metadata]
    ],
    etc.
    """
    conc_lines = [] # return concordance lines in list

    if sum(len(result.proxInfo) for result in result_set) > 10000:
        raise UserError("This query returns over 10 000 results, please try some other search terms using less-common words.", "error")

    # Empty heading
    yield {}

    ## search through each record (chapter) and identify location of search term(s)
    for result in result_set:
        ch = cdb.get_chapter(result.id)
        (book_id, chapter_num, count_prev_chap, total_word) = cdb.get_chapter_word_counts(result.id)

        for match in result.proxInfo:
            # match contains proxInfo for each word in node, find first.
            (word_id, para_chap, sent_chap) = cdb.get_word(result.id, match[0])

            conc_line = ch.get_conc_line(word_id, len(match), contextsize) + [
                [book_id, chapter_num, para_chap, sent_chap],
                [count_prev_chap + int(word_id), total_word, result.id, word_id, word_id + len(match)],
            ]

            yield conc_line
