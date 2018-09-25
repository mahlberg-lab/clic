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
