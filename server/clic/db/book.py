import psycopg2
import psycopg2.extras

from clic.db.lookup import rclass_id_lookup
from clic.tokenizer import types_from_string


def put_book(cur, book):
    """
    Import a book object:

    * name: The shortname of the book
    * content: The full book string, as per instructions in the corpora repository
    * An entry for each rclass, e.g. "chapter.text": See /schema/10-rclass.sql. A list of...
      - off_start: Character offset for start of this region
      - off_end: Character offset for end of this region, non-inclusive
      - rvalue: rvalue, e.g. chapter number (see /schema/10-rclass.sql)

    The book contents / regions will be imported into the database, and any
    "chapter.text" region will be tokenised.
    """
    rclass = rclass_id_lookup(cur)

    # Insert book / update content, get ID for other updates
    cur.execute("""
        SELECT book_id, token_tbl, region_tbl FROM book_import_init(%(name)s, %(content)s)
    """, dict(
        name=book['name'],
        content=book['content'],
    ))
    (book_id, token_tbl, region_tbl) = cur.fetchone()

    # Replace regions with new values
    for rclass_name in book.keys():
        if '.' not in rclass_name:
            continue  # Not an rclass
        rclass_id = rclass[rclass_name]
        psycopg2.extras.execute_values(cur, """
            INSERT INTO """ + region_tbl + """ (book_id, crange, rclass_id, rvalue) VALUES %s
        """, ((
            book_id,
            psycopg2.extras.NumericRange(off_start, off_end),
            rclass_id,
            rvalues[0] if len(rvalues) > 0 else None,
        ) for off_start, off_end, *rvalues in book[rclass_name]))

    # Tokenise each chapter text region and add it to the database
    psycopg2.extras.execute_values(cur, """
        INSERT INTO """ + token_tbl + """ (book_id, crange, ttype) VALUES %s
    """, ((
        book_id,
        psycopg2.extras.NumericRange(off_start, off_end),
        ttype,
    ) for ttype, off_start, off_end in types_from_string(
        book['content'],
        offset=0
    )))

    # Finalise token import, let DB update metadata, indexes
    cur.execute("""
        SELECT * FROM book_import_finalise(%(book_id)s)
    """, dict(
        book_id=book_id,
    ))


def get_book(cur, book_id_name, content=False, regions=False):
    """Get book from DB, specifying what details are required"""
    out = dict()

    # Initial fetch from main table
    cur.execute("".join([
        "SELECT book_id, name",
        ", content" if content else ", NULL AS content",
        " FROM book WHERE",
        " book_id = %s" if isinstance(book_id_name, int) else " name = %s",
    ]), (book_id_name,))
    (out['id'], out['name'], out['content'],) = cur.fetchone()
    if not content:
        del out['content']

    if regions:
        cur.execute("""
            SELECT (SELECT name FROM rclass WHERE rclass_id = r.rclass_id) rclass_name
                 , r.crange
                 , r.rvalue
              FROM region r
             WHERE r.book_id = %(book_id)s
          ORDER BY r.crange
        """, dict(
            book_id=out['id'],
        ))

        for rclass_name, crange, rvalue in cur:
            if rclass_name not in out:
                out[rclass_name] = []
            out[rclass_name].append((crange.lower, crange.upper, rvalue))

    return out
