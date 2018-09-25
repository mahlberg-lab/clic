import psycopg2
import psycopg2.extras

from clic.db.util import rclass_id


def put_book(cur, book):
    """
    Import a book object
    """
    # Insert book / update content, get ID for other updates
    cur.execute("""
        INSERT INTO book (name, content)
        VALUES (%(name)s, %(content)s)
        ON CONFLICT (name) DO UPDATE SET content=EXCLUDED.content
        RETURNING book_id
    """, dict(
        name=book['name'],
        content=book['content'],
    ))
    (book_id,) = cur.fetchone()

    # Replace tokens with new values
    cur.execute("DELETE FROM token WHERE book_id = %(book_id)s", dict(book_id=book_id))
    psycopg2.extras.execute_values(cur, """
        INSERT INTO token (book_id, crange, ttype, ordering) VALUES %s
    """, ((
        book_id,
        psycopg2.extras.NumericRange(off_start, off_end),
        ttype,
        i,
    ) for i, (rclass, ttype, off_start, off_end) in enumerate(book['regions']) if rclass == 'token.word'))

    # Replace regions with new values
    cur.execute("DELETE FROM region WHERE book_id = %(book_id)s", dict(book_id=book_id))
    psycopg2.extras.execute_values(cur, """
        INSERT INTO region (book_id, crange, rclass_id, rvalue) VALUES %s
    """, ((
        book_id,
        psycopg2.extras.NumericRange(off_start, off_end),
        rclass_id(cur, rclass),
        rvalue,
    ) for rclass, rvalue, off_start, off_end in book['regions'] if rclass != 'token.word'))
