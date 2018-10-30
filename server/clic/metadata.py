from clic.db.lookup import rclass_id_lookup


def corpora(cur):
    """
    Return a list of dicts containing:
    - id: corpus short name
    - title: corpus title
    - children: [{id: book id, title: book title, author: book author}, ...]
    """
    rclass = rclass_id_lookup(cur)

    cur.execute("""
        SELECT c.name c_name
             , c.title c_title
             , (SELECT b.name FROM book b WHERE b.book_id = cb.book_id) b_name
             , MAX(CASE WHEN bm.rclass_id = %(rclass_title)s THEN bm.content ELSE NULL END) AS title
             , MAX(CASE WHEN bm.rclass_id = %(rclass_author)s THEN bm.content ELSE NULL END) AS author
          FROM corpus c, corpus_book cb, book_metadata bm
         WHERE c.corpus_id = cb.corpus_id
           AND cb.book_id = bm.book_id
           AND bm.rclass_id IN (%(rclass_title)s, %(rclass_author)s)
      GROUP BY c.corpus_id, cb.book_id
      ORDER BY c.ordering, c.title, b_name
    """, dict(
        rclass_title=rclass['metadata.title'],
        rclass_author=rclass['metadata.author'],
    ))

    out = []
    author_book_count = {}
    for (c_id, c_title, b_id, b_title, b_author) in cur:
        if len(out) == 0 or out[-1]['id'] != 'corpus:%s' % c_id:
            out.append(dict(id='corpus:%s' % c_id, title=c_title, children=[]))
        out[-1]['children'].append(dict(id=b_id, title=b_title, author=b_author))

        # Add to the book count for this author
        if b_author not in author_book_count:
            author_book_count[b_author] = 0
        author_book_count[b_author] += 1

    out.append(dict(id=None, title='All books by author', children=[]))
    for author in sorted(author_book_count.keys()):
        out[-1]['children'].append(dict(
            id='author:%s' % author,
            title=author,
            author='%d books' % author_book_count[author],  # NB: Just doing this to get it into brackets, ew.
        ))

    return dict(corpora=out)


def corpora_headlines(cur):
    """
    Return a list of dicts containing:
    - id: corpus short name
    - title: corpus title
    - book_count: Number of books in corpus
    - word_count: Number of words in corpus
    """
    cur.execute("""
        SELECT c.name
             , c.title
             , COUNT(*) book_count
             , (SELECT SUM(word_count) FROM book_word_count bwc WHERE rclass_id = 301) word_count
          FROM corpus c, corpus_book cb
         WHERE c.corpus_id = cb.corpus_id
      GROUP BY c.corpus_id
    """)

    out = []
    for (c_id, c_title, book_count, word_count) in cur:
        out.append(dict(
            id=c_id,
            title=c_title,
            book_count=book_count,
            word_count=word_count,
        ))

    return dict(data=out)


def corpora_image(cur, corpora=[]):
    """
    Return (carousel) image for a given corpora
    """
    if len(corpora) != 1:
        raise ValueError("You must specify exactly one corpora to fetch image for")

    cur.execute("""
        SELECT c.carousel_image
          FROM corpus c
         WHERE c.name = %(name)s
    """, dict(
        name=corpora[0],
    ))

    for (carousel_image,) in cur:
        return dict(
            response=carousel_image,
            content_type='image/jpeg',
        )
