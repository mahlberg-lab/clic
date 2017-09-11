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
        clusterlength=['1']):
    # Defaults / dereference arrays
    clusterlength = int(clusterlength[0])
    subset = subset[0]

    yield dict()

    wl = cdb.get_word_list(subset, clusterlength, corpora)
    for row in wl.itertuples():
        yield row[1:-1] # Remove Index/Empty columns
