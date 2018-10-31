def region_append_without_whitespace(book, rclass, start, end, *extra):
    """
    Shrink the region (start, end) until there is no whitespace either end of
    the region. Then if it is non-zero, append the region to (rclass)
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
    """
    last_b = None
    for r in rlist:
        b = r[0]
        if last_b is None:
            if full_length:
                yield (0, b)
        else:
            yield (last_b, b)
        last_b = r[1]
    if full_length:
        yield (last_b or 0, full_length)
