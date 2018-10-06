"""Text endpoint

Return the full text for a given book.

- corpora: Book name ('AgnesG') to return. Multiple books / corpora not supported.
- regions: Region rclass(es) to return, e.g. 'quote.quote'

Parameters should be provided in querystring format, for example::

    /text?corpora=AgnesG&regions=quote.quote&regions=quote.suspension.short

Returns ``content`` with the entire book text, and a ``data`` array with the
name/lower/upper/rvalue for each region.

Examples::

    {
        "content": "It was the best of times...",
        "data": [
            ["metadata.title", 0, 11, null],
            ["metadata.author", 12, 27, null],
            ["chapter.title", 30, 52, 1],
            ["chapter.sentence", 56, 63, 2],
            ["chapter.sentence", 63, 146, 3],
            ["chapter.sentence", 146, 174, 4],
            ["chapter.sentence", 174, 397, 5],
              . . .
        ]
    }
"""
from clic.db.book import get_book
from clic.db.corpora import corpora_to_book_ids
from clic.db.lookup import rclass_id_lookup
from clic.errors import UserError


def text(cur, corpora=[], regions=[]):
    book_ids = tuple(corpora_to_book_ids(cur, corpora))
    if len(book_ids) == 0:
        raise UserError("No books to search", "error")
    rclass = rclass_id_lookup(cur)
    rclass_ids = tuple(rclass[name] for name in regions)

    if len(book_ids) > 1:
        raise UserError("Multiple books not supported", "error")

    for book_id in book_ids:
        yield ('header', {'content': get_book(cur, book_id, content=True)['content']})

    cur.execute("""
        SELECT (SELECT name FROM rclass WHERE rclass_id = r.rclass_id) rclass_name
             , r.crange
             , r.rvalue
          FROM region r
         WHERE r.book_id IN %(book_ids)s
           AND r.rclass_id IN %(rclass_ids)s
    """, dict(
        book_ids=book_ids,
        rclass_ids=rclass_ids,
    ))

    for rclass_name, crange, rvalue in cur:
        yield [rclass_name, crange.lower, crange.upper, rvalue]
