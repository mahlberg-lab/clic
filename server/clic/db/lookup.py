_tables = dict()

API_SUBSETS = dict(
    all='chapter.text',
    quote='quote.quote',
    nonquote='quote.nonquote',
    shortsus='quote.suspension.short',
    longsus='quote.suspension.long',
)


def book_id_name_lookup(cur):
    """
    Query / return book_id -> short name lookup table. Cached against process
    """
    if 'book_id' not in _tables:
        cur.execute("SELECT book_id, name FROM book")
        _tables['book_id'] = dict(cur)
    return _tables['book_id']


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
