import subprocess

REGION_COLOURS = [
    '\x1b[0m',
    '\x1b[0;37;44m',  # Blue
    '\x1b[0;37;42m',  # Green
    '\x1b[0;37;41m',  # Red
    '\x1b[0;37;45m',  # Magenta
    '\x1b[0;37;46m',  # Cyan
    '\x1b[0;37;43m',  # Yellow
]
DEFAULT_HIGHLIGHT_REGIONS = [
    'chapter.sentence',
    'quote.quote',
    'quote.suspension.short',
    'quote.suspension.long',
    'chapter.title',
    'metadata.title',
    'metadata.author',
]


def colourise_book(book, regions_to_highlight):
    """Based on algorithm in client/lib/corpora_utils"""
    inserts = [(len(book['content']), 0, False)]

    # Generate a legend
    yield "Legend:-\n"
    for i, rclass in enumerate(regions_to_highlight):
        yield REGION_COLOURS[0]
        yield "    "
        yield REGION_COLOURS[min(i + 1, len(REGION_COLOURS) - 1)]
        yield "%s\n" % rclass
    yield "-----------------------------------------------------------------------\n"

    # Generate opening/closing inserts for each region we are interested in
    for i, rclass in enumerate(regions_to_highlight):
        for r in book.get(rclass, []):
            inserts.append((r[0], i + 1, True))
            inserts.append((r[1], i + 1, False))
    inserts.sort()

    start = 0
    open_regions = {0: True}
    for insert in inserts:
        if insert[0] > start:
            for i, part in enumerate(book['content'][start:insert[0]].split("\n")):
                if i > 0:
                    yield "\n"
                # Set / reset region colours after every newline
                yield REGION_COLOURS[min(max(open_regions.keys()), len(REGION_COLOURS) - 1)]
                yield part
            start = insert[0]
        if insert[2]:
            open_regions[insert[1]] = True
        else:
            del open_regions[insert[1]]
    yield REGION_COLOURS[0]


def script_region_preview():
    """
    Given a .txt file and any region.csv file, output a version with tags coloured.
    Usage::

        # Highlight default regions within alice
        ./server/bin/region_preview corpora/ChiLit/alice.txt

        # Highlight just quote.quote regions
        ./server/bin/region_preview corpora/ChiLit/alice.txt quote.quote
    """
    import sys
    from .corpora_repo import import_book
    from ..region.tag import tagger
    from ..tokenizer import types_from_string

    book_path = sys.argv[1]
    regions_to_highlight = sys.argv[2:] if len(sys.argv) > 2 else DEFAULT_HIGHLIGHT_REGIONS

    if book_path == '-':
        book = dict(name='stdin')
        book['content'] = sys.stdin.read()
    else:
        book = import_book(book_path)
    tagger(book)

    p = subprocess.Popen(['less', '-RFi'], stdin=subprocess.PIPE)
    for out in colourise_book(book, regions_to_highlight):
        try:
            p.stdin.write(out.encode('utf8'))
        except BrokenPipeError:
            # Pager lost interest
            break
    p.communicate("")
