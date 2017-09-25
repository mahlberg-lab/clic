# -*- coding: utf-8 -*-
import os
import os.path


def concordance(cdb, corpora=['dickens'], subset=['all'], q=[], contextsize=[0]):
    """
    - corpora: List of corpora / book names
    - subset: Subset to search within, or 'all'
    - q: Quer(ies) to search for, results will contain one of the given expressions
    - contextsize: Size of context window, defaults to none.
    """
    idx = cdb.get_subset_index(subset[0])
    contextsize = contextsize[0]

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
        raise ValueError("You must supply at least one search term")

    if len(set(len(term.split()) for term in q)) > 1:
        raise ValueError("We don't support multiple terms of varying lengths")

    term_clauses = []
    for term in q:
        term_clauses.append('c3.{0} = "{1}"'.format(idxName, term))

    ## conduct database search
    ## note: /proxInfo needed to search individual books
    query = '(%s) and/proxInfo (%s)' % (
        cdb.corpora_list_to_query(corpora),
        ' or '.join(term_clauses),
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
        raise ValueError("This query returns over 10 000 results, please try some other search terms using less-common words.")

    # Empty heading
    yield {}

    # NB: We should re-calculate for each match, but we check length in build_query
    node_size = len(q[0].split())

    ## search through each record (chapter) and identify location of search term(s)
    for result in result_set:
        ch = cdb.get_chapter(result.id)
        (count_prev_chap, total_word) = cdb.get_chapter_word_counts(ch.book, int(ch.chapter))

        for match in result.proxInfo:
            (word_id, para_chap, sent_chap) = ch.get_word(match)

            conc_line = ch.get_conc_line(word_id, node_size, contextsize) + [
                [ch.book, ch.chapter, str(para_chap), str(sent_chap)],
                [count_prev_chap + int(word_id), total_word, result.id, word_id, word_id + node_size],
            ]

            yield conc_line
