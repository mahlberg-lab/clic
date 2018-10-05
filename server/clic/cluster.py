'''
Return a list of word clusters, and their frequency within the given texts.

- corpora: 1+ corpus name (e.g. 'dickens') or book name ('AgnesG') to search within
- subset: subset to search through, one of shortsus/longsus/nonquote/quote/all. Default 'all' (i.e. all text)
- clusterlength: cluster length to search for, one of 1/3/4/5 (NB: There is no 2). Default 1
- cutoff: The cutoff frequency, if an cluster occurs less times than this it is not returned. Default '5'

Parameters should be provided in querystring format, for example::

    ?corpora=dickens&corpora=AgnesG&subset=quote&clusterlength=5

Returns a ``data`` array, one entry per result. Each item is an array of ``[cluster, frequency]``.

The ``version`` object gives both the current version of CLiC and the revision of the
corpora ingested in the database.

Examples:

/api/cluster?corpora=AgnesG&subset=longsus::

    {
        "data":[
            ["a",13],
            ["said",13],
            ["she",16],
            ["i",13],
            ["and",12],
            ["the",13],
            ["of",6],
            ["replied",6],
            ["to",9],
            ["in",5],
            ["as",6],
            ["her",7],
            ["it",6],
            ["he",7],
            ["my",7]
        ],
        "message": {
            "message":"199 clusters with a frequency less than 5 are not shown",
            "level":"info",
            "stack":null,
            "error":"UserError"
        },
        "version":{"corpora":"master:2affe56","clic:import":"1.6:876222b","clic":"v1.6.1"}
    }

http://clic.bham.ac.uk/api/cluster?corpora=AgnesG&clusterlength=3::

    {
        "data":[
            ["i could not",35],
            ["as well as",21],
            ["i did not",23],
             . . .
        ],
        "message": {
            "message":"56566 clusters with a frequency less than 5 are not shown",
            "level":"info",
            "stack":null,
            "error":"UserError"
        },
        "version":{"corpora":"master:2affe56","clic:import":"1.6:876222b","clic":"v1.6.1"}
    }
'''
from clic.db.corpora import corpora_to_book_ids
from clic.db.lookup import api_subset_lookup


def cluster(
        cur,
        subset=['all'], corpora=['dickens'],
        clusterlength=['1'],
        cutoff=None):
    # Defaults / dereference arrays
    book_ids = corpora_to_book_ids(cur, corpora)
    clusterlength = int(clusterlength[0])
    api_subset = api_subset_lookup(cur)
    rclass_ids = tuple(api_subset[s] for s in subset if s != 'all')

    # Choose cutoff
    if cutoff is not None:
        cutoff = int(cutoff[0])
    else:
        cutoff = 5 if len(book_ids) > 1 else 2

    skipped = 0
    wl = get_word_list(cur, book_ids, rclass_ids, clusterlength)

    for term, freq in wl:
        if freq >= cutoff:
            yield (term, freq)
        else:
            skipped += 1

    if skipped > 0:
        yield ('footer', dict(info=dict(
            message='%d clusters with a frequency less than %d are not shown' % (skipped, cutoff)
        )))


def get_word_list(cur, book_ids, rclass_ids, clusterlength):
    """
    Yields tuples of:
    - Concatenated tokens
    - Frequency of them in given text
    """
    params = dict(
        book_ids=tuple(book_ids),
        extra_tokens=clusterlength - 1,
    )
    query = """
        SELECT ttypes
             , COUNT(*)
          FROM (
            SELECT book_id
                 , STRING_AGG(ttype, ' ') OVER (ORDER BY book_id, LOWER(crange) ROWS BETWEEN %(extra_tokens)s PRECEDING AND CURRENT ROW) ttypes
                 , BOOL_AND(ttype IS NOT NULL) OVER (ORDER BY book_id, LOWER(crange) ROWS BETWEEN %(extra_tokens)s PRECEDING AND CURRENT ROW) ngram_valid
              FROM (
                SELECT t.book_id, t.crange, t.ttype
                  FROM token t
                 WHERE book_id IN %(book_ids)s
    """
    if len(rclass_ids) > 0:
        # Make sure these tokens are in an appropriate region
        query += """
                   AND EXISTS(SELECT 1
                                FROM token_metadata tm
                               WHERE t.book_id = tm.book_id
                                 AND LOWER(t.crange) = tm.lower_crange
                                 AND tm.part_of ? %(rclass_id)s)
        """
        params['rclass_id'] = str(rclass_ids[0])
        if len(rclass_ids) > 1:
            raise NotImplementedError()
    query += """
                    UNION ALL
                SELECT r.book_id, r.crange, NULL ttype
                  FROM region r
                 WHERE book_id IN %(book_ids)s
                   ) regions_and_tokens
               ) all_ngrams
         WHERE ngram_valid
      GROUP BY ttypes
    """
    cur.execute(query, params)
    return cur
