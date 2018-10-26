import psycopg2
import psycopg2.extras

from clic.db.lookup import rclass_id_lookup, api_subset_lookup
from clic.tokenizer import types_from_string


def put_book(cur, book):
    """
    Import a book object
    - name: The shortname of the book
    - content: The full book string, as per instructions in the corpora repository
    - An entry for each rclass, e.g. "chapter.text": See /schema/10-rclass.sql. A list of...
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
    for rclass_name, _, off_start, off_end in book['regions']:
        if rclass_name != 'chapter.text':
            continue
        psycopg2.extras.execute_values(cur, """
            INSERT INTO """ + token_tbl + """ (book_id, crange, ttype) VALUES %s
        """, ((
            book_id,
            psycopg2.extras.NumericRange(off_start, off_end),
            ttype,
        ) for ttype, off_start, off_end in types_from_string(
            book['content'][off_start:off_end],
            offset=off_start
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


def get_book_metadata(cur, book_ids, metadata):
    """
    Generate dict of metadata that should go in footer of both concordance and subsets
    - book_ids: Array of book IDs to include
    - metadata: Metadata items to include, a set contining some of...
      - 'book_titles': The title / author of each book
      - 'chapter_start': The start character for all chapters, and end of book
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
                SELECT b.name
                     , bm.rclass_id
                     , bm.content
                  FROM book b, book_metadata bm
                 WHERE b.book_id = bm.book_id
                   AND b.book_id IN %s
                   AND bm.rclass_id IN %s
            """, (
                tuple(book_ids),
                (rclass['metadata.title'], rclass['metadata.author']),
            ))
            for (book_name, rclass_id, content) in cur:
                if book_name not in out[k]:
                    out[k][book_name] = [None, None]
                out[k][book_name][0 if rclass_id == rclass['metadata.title'] else 1] = content

        elif k == 'chapter_start':
            cur.execute("""
                SELECT b.name
                     , r.rvalue as chapter_num
                     , r.crange crange
                  FROM book b, region r
                 WHERE b.book_id = r.book_id
                   AND r.rclass_id = %s
                   AND b.book_id IN %s
            """, (
                rclass['chapter.text'],
                tuple(book_ids),
            ))
            for (book_name, chapter_num, crange) in cur:
                if book_name not in out[k]:
                    out[k][book_name] = dict()
                out[k][book_name][chapter_num] = crange.lower
                out[k][book_name]['_end'] = max(out[k][book_name].get('_end', 0), crange.upper)

        elif k == 'word_count_chapter':
            cur.execute("""
                SELECT b.name
                     , bwc.rvalue as chapter_num
                     , bwc.word_count
                  FROM book b, book_word_count bwc
                 WHERE b.book_id = bwc.book_id
                   AND bwc.rclass_id = %s
                   AND b.book_id IN %s
              ORDER BY bwc.book_id, bwc.rvalue
            """, (
                rclass['chapter.text'],
                tuple(book_ids),
            ))
            for (book_name, chapter_num, word_total) in cur:
                if book_name not in out[k]:
                    out[k][book_name] = dict(_end=0)
                out[k][book_name][chapter_num] = out[k][book_name]['_end']
                out[k][book_name]['_end'] += int(word_total)

        elif k.startswith('word_count_'):
            api_subset = api_subset_lookup(cur)
            # TODO: word_count_quote not quite matching old CLiC (too high). Why?
            cur.execute("""
                SELECT b.name
                     , SUM(bwc.word_count) AS word_count
                  FROM book b, book_word_count bwc
                 WHERE b.book_id = bwc.book_id
                   AND bwc.rclass_id = %s
                   AND b.book_id IN %s
              GROUP BY b.book_id
            """, (
                api_subset[k.replace('word_count_', '')],
                tuple(book_ids),
            ))
            for (book_name, word_count) in cur:
                out[k][book_name] = int(word_count)

        else:
            raise ValueError("Unknown metadata item %s" % k)

    return out
