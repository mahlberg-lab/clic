# -*- coding: utf-8 -*-
"""Subset endpoint

Returns subsets of given texts, for example quotations.

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: subset to return, one of shortsus/longsus/nonquote/quote/all. Default 'all' (i.e. all text)
- contextsize: Size of context window around subset. Default 0.

Parameters should be provided in querystring format, for example::

    ?corpora=dickens&corpora=AgnesG&subset=quote

Returns a ``data`` array, one entry per result. Each item is an array with the following items:

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

Examples:

/api/subset?corpora=AgnesG&subset=longsus::

    {"data":[
      [["observed"," ","Smith",";"," ","'","and"," ","a"," ","darksome"," ",[0,2,6,8,10]], . . .],
      [["replied"," ","she",","," ","with"," ","a"," ","short",","," ","bitter"," ","laugh",";"," ",[0,2,5,7,9,12,14]], . . .],
       . . .
    ]}

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
    ]}

"""
def subset(cdb, corpora=['dickens'], subset=['quote'], contextsize=['0']):
    """
    Main entry function for subset search

    - corpora: List of corpora / book names
    - subset: Subset(s) to search for.
    - contextsize: Size of context window, defaults to none.
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
            (book_id, chapter_num, count_prev_chap, total_word) = cdb.get_chapter_word_counts(chapter_id)

        (_, para_chap, sent_chap) = cdb.get_word(chapter_id, [0, offset_start])
        yield ch.get_conc_line(offset_start, offset_end - offset_start, contextsize) + [
                [book_id, chapter_num, para_chap, sent_chap],
                [count_prev_chap + int(offset_start), total_word, chapter_id, offset_start, offset_end],
        ]
