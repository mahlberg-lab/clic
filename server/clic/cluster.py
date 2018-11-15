"""
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

Method
------

The cluster search peforms the following steps:

1. Resolve the corpora option to a list of book IDs, translate the subset
   selection to a database region. If the subset 'all' is selected, use
   chapters as our region.

2. Form a list of both tokens in the selected region. Order these by their
   overall position in book.

3. Consider each (clusterlength) set of items in the list. If there are any
   gaps in their overall position, we discard the cluster. This means:

   * Clusters will span adjacent regions, e.g. a cluster spanning 2 quotes will
     be included.
   * Clusters will not span 2 adjacent chapters, since the chapter title tokens
     will cause a gap in the tokens.

4. For the remaining clusters, count instances of each unique cluster, applying
   frequency cut-off before returning result.

Examples / edge cases
---------------------

These are the corpora we use for the following tests::

    >>> db_cur = test_database(
    ... alice='''
    ... Alice’s Adventures in Wonderland
    ... Lewis Carroll
    ...
    ... CHAPTER I. Down the Rabbit-Hole
    ...
    ... Alice was beginning to get very tired of sitting by her sister on the
    ... bank, and of having nothing to do:
    ... '''.strip(),
    ... willows='''
    ... The Wind in the Willows
    ... Kenneth Grahame
    ...
    ...
    ... CHAPTER I. THE RIVER BANK
    ...
    ... The Rat said nothing, but stooped and unfastened a rope and hauled
    ... on it; then lightly stepped into a little boat which the Mole had not
    ... observed. It was painted blue outside and white within, and was just the
    ... size for two animals; and the Mole’s whole heart went out to it at once,
    ... even though he did not yet fully understand its uses.
    ...
    ... ‘This has been a wonderful day!’ said he, as the Rat shoved off and took
    ... to the sculls again. ‘Do you know, I’ve never been in a boat before in
    ... all my life.’
    ...
    ... ‘What?’ cried the Rat, open-mouthed: ‘Never been in a--you never--well
    ... I--what have you been doing, then?’
    ...
    ... ‘Is it so nice as all that?’ asked the Mole shyly, though he was quite
    ... prepared to believe it as he leant back in his seat and surveyed the
    ... cushions, the oars, the rowlocks, and all the fascinating fittings, and
    ... felt the boat sway lightly under him.
    ...
    ... CHAPTER II. THE OPEN ROAD
    ...
    ...
    ... ‘Ratty,’ said the Mole suddenly, one bright summer morning, ‘if you
    ... please, I want to ask you a favour.’
    ...
    ... '''.strip())

Searching for all clusters and filtering for ones with "mole" in, we see that
"the Mole" and "the Mole's" count as different clusters::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['all'], clusterlength=['2'], cutoff=['0'])) if 'mole' in x[0]]
    [('mole had', 1), ('mole shyly', 1), ('mole suddenly', 1),
     ("mole's whole", 1), ('the mole', 3), ("the mole's", 1)]

Instances of "The Rat" and "the Rat" are combined though, since the types ignore case::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['all'], clusterlength=['2'], cutoff=['0'])) if 'rat' in x[0]]
    [('rat open-mouthed', 1), ('rat said', 1), ('rat shoved', 1), ('ratty said', 1),
     ('the rat', 3)]

There are no clusters with "willows" or "chapter" in, as they are outside the
chapter text::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['all'], clusterlength=['2'], cutoff=['0'])) if 'willows' in x[0]]
    []
    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['all'], clusterlength=['2'], cutoff=['0'])) if 'chapter' in x[0]]
    []

Paragraphs aren't considered a boundary, as "Life.’ / ‘What" (2nd--3rd
paragraph) is a cluster::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['all'], clusterlength=['2'], cutoff=['0'])) if 'life' in x[0]]
    [('life what', 1), ('my life', 1)]

...however, "him ‘Ratty" (Ch 1-- Ch 2) is not, the chapter title is in the way::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['all'], clusterlength=['2'], cutoff=['0'])) if 'ratty' in x[0]]
    [('ratty said', 1)]

When selecting across all text, quotes are not considered boundaries::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['all'], clusterlength=['2'], cutoff=['0'])) if 'day' in x[0]]
    [('day said', 1), ('wonderful day', 1)]

But if we only select within quotes, we do not span to the next quote::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['quote'], clusterlength=['2'], cutoff=['0'])) if 'day' in x[0]]
    [('wonderful day', 1)]

We do not treat end-of-quotes as a boundary. If quotes are adjacent then we
will get a cluster that straddles the quote boundary in the 3rd and 4th
paragraph::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['willows'],
    ...   subset=['quote'], clusterlength=['2'], cutoff=['0'])) if 'then' in x[0]]
    [('doing then', 1), ('then is', 1)]

We do not form clusters across books when selecting multiple books::

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['alice', 'willows'],
    ...   subset=['nonquote'], clusterlength=['2'], cutoff=['0'])) if 'nothing' in x[0]]
    [('having nothing', 1), ('nothing but', 1),
     ('nothing to', 1), ('said nothing', 1)]

    >>> [x for x in format_cluster(cluster(db_cur, corpora=['alice', 'willows'],
    ...   subset=['nonquote'], clusterlength=['2'], cutoff=['0'])) if 'alice' in x[0]]
    [('alice was', 1)]

"""
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
    rclass_ids = tuple(api_subset[s] for s in subset)

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
    if len(rclass_ids) != 1:
        raise NotImplementedError()

    query = """
        SELECT ttypes
             , COUNT(*)
          FROM (
            SELECT book_id
                 , STRING_AGG(ttype, ' ') OVER (ORDER BY book_id, ordering, ttype ROWS BETWEEN %(extra_tokens)s PRECEDING AND CURRENT ROW) ttypes
                 , MIN(ordering) OVER (ORDER BY book_id, ordering, ttype ROWS BETWEEN %(extra_tokens)s PRECEDING AND CURRENT ROW) min_ordering
                 , MAX(ordering) OVER (ORDER BY book_id, ordering, ttype ROWS BETWEEN %(extra_tokens)s PRECEDING AND CURRENT ROW) max_ordering
                 , COUNT(ttype) OVER (ORDER BY book_id, ordering, ttype ROWS BETWEEN %(extra_tokens)s PRECEDING AND CURRENT ROW) ttype_count
              FROM token t
             WHERE book_id IN %(book_ids)s
               AND t.part_of ? %(rclass_id)s
               ) all_ngrams
         WHERE max_ordering - min_ordering = %(extra_tokens)s
           AND ttype_count = %(extra_tokens)s + 1
               -- NB: Technically we should check to see if they are all part of the same book, but in practice books aren't going to be short enough to trigger it
      GROUP BY ttypes
    """
    params = dict(
        book_ids=tuple(book_ids),
        extra_tokens=clusterlength - 1,
        rclass_id=str(rclass_ids[0]),
    )
    cur.execute(query, params)
    return cur
