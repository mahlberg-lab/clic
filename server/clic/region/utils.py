def region_append_without_whitespace(book, rclass, start, end, *extra):
    """
    Shrink the region (start, end) until there is no whitespace either end of
    the region. Then if it is non-zero, append the region to (rclass)

    Return true iff a region is added.
    """
    if start is None:
        return

    if start >= len(book['content']):
        return (-1, -1) + extra  # Outside the range, return something that will get ignored

    while book['content'][start].isspace():
        start += 1
        if start >= len(book['content']):
            # Fallen off the end of the book, this isn't a useful region
            return

    while book['content'][end - 1].isspace():
        end -= 1
        if end < 0:
            # Fallen off the start of the book, this isn't a useful region
            return

    if end > start:
        if rclass not in book:
            book[rclass] = []
        book[rclass].append((start, end) + extra)
        return True
    return False


def regions_invert(rlist, full_length=None):
    """
    Given a list of regions, return the inverse. If full_length not given, ignore first and last extremities

        >>> list(regions_invert([], 100))
        [(0, 100)]

        >>> list(regions_invert([]))
        []

        >>> list(regions_invert([(10, 20), (50, 60)], 100))
        [(0, 10), (20, 50), (60, 100)]

        >>> list(regions_invert([(10, 20), (50, 60)]))
        [(20, 50)]

        >>> list(regions_invert([(0, 0), (10, 15), (15, 20), (50, 50)], 100))
        [(0, 10), (20, 50), (50, 100)]
    """
    last_b = None
    for r in rlist:
        b = r[0]
        if last_b is None:
            if full_length and b > 0:
                yield (0, b)
        elif b > last_b:
            yield (last_b, b)
        last_b = r[1]
    if full_length and full_length > (last_b or 0):
        yield (last_b or 0, full_length)


def regions_flatten(book):
    """
    Flatten a book's regions down to a single array-of-arrays, suitable for exporting
    """
    def short_string(s):
        return s if len(s) < 40 else s[0:20] + '...' + s[-20:]

    out = []
    for rclass in book.keys():
        if rclass == 'name':
            continue
        if rclass == 'content':
            continue
        for r in book[rclass]:
            out.append((
                rclass,
                r[0],
                r[1],
                r[2] if len(r) > 2 else None,
                short_string(book['content'][r[0]:r[1]]),
            ))
    # Sort by start ascending, then end descending
    return sorted(out, key=lambda x: (x[1], -x[2], x[0]))


def regions_unflatten(regions):
    """
    Reverse regions_flatten, return a dict to update a book with. For example::

        book.update(regions_unflatten(regions))
    """
    out = {}
    for r in regions:
        if r[0] not in out:
            out[r[0]] = []
        out[r[0]].append((
            int(r[1]),  # Start
            int(r[2]),  # End
        ) if r[3] is None or r[3] == '' else (
            int(r[1]),  # Start
            int(r[2]),  # End
            int(r[3]),  # rvalue
        ))
    return out
