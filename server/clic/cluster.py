'''
Return a word-list cluster

[
    Type,
    Raw facet,
    Count,
    Percentage,
]
'''
from clic.errors import UserError

def cluster(
        cdb,
        subset=['quote'], corpora=['dickens'],
        clusterlength=['1'],
        cutoff=['5']):
    # Defaults / dereference arrays
    clusterlength = int(clusterlength[0])
    subset = subset[0]
    cutoff = int(cutoff[0])

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
