'''
Return a word-list cluster

[
    Type,
    Raw facet,
    Count,
    Percentage,
]
'''
def cluster(
        cdb,
        subset=['quote'], corpora=['dickens'],
        clusterlength=['1'],
        cutoff=['5']):
    # Defaults / dereference arrays
    clusterlength = int(clusterlength[0])
    subset = subset[0]
    cutoff = int(cutoff[0])

    yield dict()

    wl = cdb.get_word_list(subset, clusterlength, corpora)
    for term, (termId, nRecs, freq) in wl:  # facet = (thing, thing, frequency)
        if freq >= cutoff:
            yield (term, freq)
