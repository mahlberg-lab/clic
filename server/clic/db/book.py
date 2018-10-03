import psycopg2
import psycopg2.extras

from clic.db.lookup import rclass_id_lookup, api_subset_lookup


def put_book(cur, book):
    """
    Import a book object
    """
    rclass = rclass_id_lookup(cur)

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
    ) for i, (rclass_name, ttype, off_start, off_end) in enumerate(book['regions']) if rclass_name == 'token.word'))

    # Replace regions with new values
    cur.execute("DELETE FROM region WHERE book_id = %(book_id)s", dict(book_id=book_id))
    psycopg2.extras.execute_values(cur, """
        INSERT INTO region (book_id, crange, rclass_id, rvalue) VALUES %s
    """, ((
        book_id,
        psycopg2.extras.NumericRange(off_start, off_end),
        rclass[rclass_name],
        rvalue,
    ) for rclass_name, rvalue, off_start, off_end in book['regions'] if rclass_name != 'token.word'))


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

    rclass = rclass_id_lookup(cur)

    out = {}
    for k in metadata:
        out[k] = {}

        if k == 'book_titles':
            cur.execute("""
                SELECT book_id, rclass_id, content
                  FROM book_metadata
                 WHERE book_id IN %s
                   AND rclass_id IN %s
            """, (
                tuple(book_ids),
                (rclass['metadata.title'], rclass['metadata.author']),
            ))
            for (book_id, rclass_id, content) in cur:
                if book_id not in out[k]:
                    out[k][book_id] = [None, None]
                out[k][book_id][0 if rclass_id == rclass['metadata.title'] else 1] = content

        elif k == 'chapter_start':
            cur.execute("""
                SELECT bwc.book_id, bwc.rvalue as chapter_num, bwc.word_count
                  FROM book_word_count bwc
                 WHERE bwc.rclass_id = %s
                   AND bwc.book_id IN %s
              ORDER BY bwc.book_id, bwc.rvalue
            """, (
                rclass['chapter.text'],
                tuple(book_ids),
            ))
            for (book_id, chapter_num, word_total) in cur:
                if book_id not in out[k]:
                    out[k][book_id] = dict(_end=0)
                out[k][book_id][chapter_num] = out[k][book_id]['_end']
                out[k][book_id]['_end'] += word_total

        elif k == 'word_count_all':
            cur.execute("""
                SELECT bwc.book_id, SUM(bwc.word_count) AS word_count
                  FROM book_word_count bwc
                 WHERE bwc.rclass_id = %s
                   AND bwc.book_id IN %s
              GROUP BY bwc.book_id
            """, (
                rclass['chapter.text'],
                tuple(book_ids),
            ))
            for (book_id, word_count) in cur:
                out[k][book_id] = word_count

        elif k.startswith('word_count_'):
            api_subset = api_subset_lookup(cur)
            # TODO: word_count_quote not quite matching old CLiC (too high). Why?
            cur.execute("""
                SELECT bwc.book_id, SUM(bwc.word_count) AS word_count
                  FROM book_word_count bwc
                 WHERE bwc.rclass_id = %s
                   AND bwc.book_id IN %s
              GROUP BY bwc.book_id
            """, (
                api_subset[k.replace('word_count_', '')],
                tuple(book_ids),
            ))
            for (book_id, word_count) in cur:
                out[k][book_id] = word_count

        else:
            raise ValueError("Unknown metadata item %s" % k)

    return out
