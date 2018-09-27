OLD_ALIASES = dict(
    dickens='corpus:DNov',
    ntc='corpus:19C',
    ChiLit='corpus:ChiLit',
    Other='corpus:ArTs',
)


def corpora_to_book_ids(cur, corpora):
    """
    Resolve list of corpora into set of book IDs. Where corpora could be:
    - (book_name): Fetch relevant book ID
    - "corpra:DNov": All books in that corpora
    - "author:Thomas Hardy" All books by that author
    """
    out = []
    for c in corpora:
        if isinstance(c, int):
            # It's already a Book ID, pass through
            out.append(int)
        elif c in OLD_ALIASES:
            # Old bare corpora names should still be handled
            out.extend(corpora_to_book_ids(cur, OLD_ALIASES[c]))
        elif c.startswith('corpus:'):
            cur.execute("""
              SELECT cb.book_id
                FROM corpus c, corpus_book cb
               WHERE c.corpus_id = cb.corpus_id
                 AND name = %s
            """, (c[len('corpus:'):],))
            out.extend([r[0] for r in cur])
        elif c.startswith('author:'):
            cur.execute("""
              SELECT bm.book_id
                FROM book_metadata bm
               WHERE bm.author = %s
            """, (c[len('author:'):],))
            out.extend([r[0] for r in cur])

            c = c[7:]
            cur.execute("""
            """, )
            out.extend(corpora_to_book_ids(cur, ))
        else:
            # Assume book name
            cur.execute("SELECT book_id FROM book WHERE name = %s", (c,))
            out.extend([r[0] for r in cur])
    return out
