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

    # Refresh materialized views
    cur.execute("SELECT refresh_book_materialized_views()")


def get_book(cur, book_id, content=False, tokens=False, regions=False):
    """Get book from DB, specifying what details are required"""
    out = dict(id=book_id)

    # Initial fetch from main table
    cur.execute("SELECT name, " + ("content" if content else "NULL") + " AS content FROM book WHERE book_id = %s", (book_id,))
    (out['name'], out['content'],) = cur.fetchone()
    if not content:
        del out['content']

    if tokens:
        raise NotImplementedError()
    if regions:
        raise NotImplementedError()

    return out


def get_book_metadata(cur, book_ids, metadata):
        """
        Generate dict of metadata that should go in footer of both concordance and subsets
        - book_ids: Array of book IDs to include
        - metadata: Metadata items to include, a set contining some of...
          - 'book_titles': The title / author of each book
          - 'chapter_start': The start word ID for all achpters (i.e. the length of the previous)
          - 'word_count_(subset)': Count of words within (subset)
        """
        def p_params(*args):
            return ("?, " * sum(len(x) for x in args)).rstrip(', ')

        out = {}
        # TODO: Rewrite me
        for k in metadata:
            out[k] = {}

            if k == 'book_titles':
                for (book_id, title, author) in self.rdb_query(
                        "SELECT book_id, title, author FROM book" +
                        " WHERE book_id IN (" + p_params(book_ids) + ")",
                        tuple(book_ids)):
                    out[k][book_id] = (title, author)

            elif k == 'chapter_start':
                for (book_id, chapter_num, word_total) in self.rdb_query(
                        "SELECT book_id, chapter_num, word_total FROM chapter" +
                        " WHERE book_id IN (" + p_params(book_ids) + ")" +
                        " ORDER BY 1, 2",
                        tuple(book_ids)):
                    if book_id not in out[k]:
                        out[k][book_id] = dict(_end=0)
                    out[k][book_id][chapter_num] = out[k][book_id]['_end']
                    out[k][book_id]['_end'] += word_total

            elif k == 'word_count_all':
                for (book_id, word_count) in self.rdb_query(
                        "SELECT book_id, SUM(word_total) word_count FROM chapter" +
                        " WHERE book_id IN (" + p_params(book_ids) + ")" +
                        " GROUP BY 1 ORDER BY 1",
                        tuple(book_ids)):
                    out[k][book_id] = word_count

            elif k.startswith('word_count_'):
                for (book_id, word_count) in self.rdb_query(
                        "SELECT c.book_id" +
                        "     , SUM(s.offset_end - s.offset_start) word_count" +
                        "  FROM subset s, chapter c" +
                        " WHERE s.chapter_id = c.chapter_id" +
                        "   AND book_id IN (" + p_params(book_ids) + ")" +
                        "   AND s.subset_type = ?" +
                        " GROUP BY 1 ORDER BY 1",
                        tuple(book_ids) + (k.replace('word_count_', ''), )):
                    out[k][book_id] = word_count

            else:
                raise ValueError("Unknown metadata item %s" % k)

        return out
