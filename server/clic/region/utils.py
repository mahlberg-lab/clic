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
