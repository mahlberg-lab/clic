# -*- coding: utf-8 -*-
import os
import os.path


def concordance(cdb, corpora=['dickens'], subset='all', type='whole', q=None):
    """
    - q: Query to search for
    - corpora: List of corpora / book names
    - subset: Subset to search within, or 'all'
    - type: ``whole`` expression, or ``any`` word within.
    """
    return create_concordance(
        cdb,
        q[0],
        dict(
            shortsus='shortsus-idx',
            longsus='longsus-idx',
            nonquote='non-quote-idx',
            quote='quote-idx',
            all='chapter-idx',
        )[subset[0]],
        corpora,
        type[0],
    )


def build_query(cdb, terms, idxName, Materials, selectWords):
    '''
    Builds a cheshire query
     - terms: Search terms (space separated?)
     - idxName: Index to use, e.g. "chapter-idx"
     - Materials: List of subcorpi to search, e.g. ["dickens"]
     - selectWords: "whole" / "any"

    Its output is a tuple of which the first element is a query.
    the second element is number of search terms in the query.
    '''

    subcorpus = []
    corpus_names = cdb.get_corpus_names()
    for m in Materials:
        subcorpus.append('c3.{0} = "{1}"'.format(
            'subCorpus-idx' if m in corpus_names else 'book-idx',
            m,
        ))

    ## search whole phrase or individual words?
    if selectWords == "whole":
        # for historic purposes: number_of_search_terms was originally nodeLength
        number_of_search_terms = len(terms.split())
        terms = [terms]
    else:
        #FIXME is this correct in case of an AND search?
        number_of_search_terms = 1
        terms = terms.split()

    ## define search term
    term_clauses = []
    for term in terms:
        term_clauses.append('c3.{0} = "{1}"'.format(idxName, term))

    ## conduct database search
    ## note: /proxInfo needed to search individual books
    query = '(%s) and/proxInfo (%s)' % (
        ' or '.join(subcorpus),
        ' or '.join(term_clauses),
    )

    return query, number_of_search_terms


def create_concordance(cdb, terms, idxName, Materials, selectWords):
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
    query, number_of_search_terms = build_query(cdb, terms, idxName, Materials, selectWords)
    result_set = cdb.c3_query(query)

    conc_lines = [] # return concordance lines in list
    word_window = 10 # word_window is set to 10 by default - on both sides of node

    if sum(len(result.proxInfo) for result in result_set) > 10000:
        raise ValueError("This query returns over 10 000 results, please try some other search terms using less-common words.")

    ## search through each record (chapter) and identify location of search term(s)
    for result in result_set:
        ch = cdb.get_chapter(result.id)
        (count_prev_chap, total_word) = cdb.get_chapter_word_counts(ch.book, int(ch.chapter))

        for match in result.proxInfo:
            (word_id, para_chap, sent_chap) = ch.get_word(match)

            conc_line = ch.get_conc_line(word_id, number_of_search_terms, word_window) + [
                [ch.book, ch.chapter, str(para_chap), str(sent_chap)],
                [count_prev_chap + int(word_id), total_word],
            ]

            conc_lines.append(conc_line)

    return conc_lines
