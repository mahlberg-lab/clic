_rclass = None


def rclass_id(cur, rclass_name):
    """
    Return rclass_id for given (rclass_name), caching the lot in an instance
    variable.
    """
    global _rclass
    if not _rclass:
        _rclass = {}
        cur.execute("SELECT rclass_id, name FROM rclass")
        for rclass_id, name in cur:
            _rclass[name] = rclass_id
    return _rclass[rclass_name]


def corpra_to_book_ids(cur, corpora):
    """
    Convert a list of corpora/book/authors into book_ids
    """
    # TODO: Cheat and return all books
    cur.execute("SELECT book_id FROM book")
    return [x[0] for x in cur]


def subset_to_rclass_id(cur, subset):
    """
    Convert shortsus/longsus/nonquote/quote/all to rclass_id, or None for all
    """
    # TODO: Cheat and assume all
    return None
