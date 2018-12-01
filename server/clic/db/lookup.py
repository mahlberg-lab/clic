'''
clic.db.lookup: Translate forms of region class
***********************************************
'''
_tables = dict()

#: Translate public API subset names back to regions
API_SUBSETS = dict(
    all='chapter.text',
    quote='quote.quote',
    nonquote='quote.nonquote',
    shortsus='quote.suspension.short',
    longsus='quote.suspension.long',
)


def rclass_id_lookup(cur):
    """
    Return a lookup of rclass name -> rclass_id
    """
    if 'rclass_id' not in _tables:
        cur.execute("SELECT name, rclass_id FROM rclass")
        _tables['rclass_id'] = dict(cur)
    return _tables['rclass_id']


def api_subset_lookup(cur):
    """
    Return a lookup of API subset names -> rclass_id
    """
    if 'api_subset' not in _tables:
        rclass = rclass_id_lookup(cur)
        _tables['api_subset'] = dict((k, rclass[v]) for k, v in API_SUBSETS.items())
    return _tables['api_subset']
