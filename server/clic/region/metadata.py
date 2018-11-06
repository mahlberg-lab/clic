"""
Add metadata.* tags to regions.

metadata.title / metadata.author regions
----------------------------------------

If there are 2 lines at the start, with an empty line after, we treat this as a
title / author combination::

    >>> run_tagger('''
    ... Fly Fishing
    ... J R Hartley
    ...
    ... INTRODUCTION.
    ...
    ... Fly Fishing: Memories of Angling Days, also published as Fly Fishing by
    ... '''.strip(), tagger_metadata)
    [('metadata.title', 0, 11, None, 'Fly Fishing'),
     ('metadata.author', 12, 23, None, 'J R Hartley')]

Anything that doesn't match this gets ignored::

    >>> run_tagger('''
    ... Fly Fishing
    ... J R Hartley
    ... INTRODUCTION.
    ...
    ... Fly Fishing: Memories of Angling Days, also published as Fly Fishing by
    ... '''.strip(), tagger_metadata)
    []

"""
import re

TITLE_AUTHOR_REGEX = re.compile(r'^(.+)\n(.+)\n\n')


def tagger_metadata(book):
    """
    Add metadata.* tags to regions
    """
    m = re.match(TITLE_AUTHOR_REGEX, book['content'])
    if not m:
        # Can't find title/author, nothing to do
        return

    if len(book.get('metadata.title', [])) == 0:
        # Title (should) be first line
        book['metadata.title'] = [m.span(1)]

    if len(book.get('metadata.author', [])) == 0:
        # Author (should) be second line
        book['metadata.author'] = [m.span(2)]
