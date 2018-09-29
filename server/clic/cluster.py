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
from clic.errors import UserError


def cluster(
        cdb,
        subset=['all'], corpora=['dickens'],
        clusterlength=['1'],
        cutoff=None):
    # Defaults / dereference arrays
    clusterlength = int(clusterlength[0])
    subset = subset[0]

    # Choose cutoff
    if cutoff is not None:
        cutoff = int(cutoff[0])
    elif len(corpora) == 1:
        # If only one item, have a low cut-off if this is a book
        is_corpus = cdb.rdb_query("SELECT COUNT(*) FROM corpus WHERE corpus_id = ?", (corpora[0],)).fetchone()[0] > 0
        cutoff = 5 if is_corpus else 2
    else:
        cutoff = 5

    skipped = 0
    wl = cdb.get_word_list(subset, clusterlength, corpora)

    yield dict()

    for term, (termId, nRecs, freq) in wl:  # facet = (thing, thing, frequency)
        if freq >= cutoff:
            yield (term, freq)
        else:
            skipped += 1
    if skipped > 0:
        raise UserError('%d clusters with a frequency less than %d are not shown' % (skipped, cutoff), 'info')
