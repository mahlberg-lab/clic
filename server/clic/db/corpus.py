def put_corpus(cur, corpus):
    """
    Add a corpus (i.e. a set of books) object to the database.

    A corpus object is a dict containing
    - name: Short name of corpus
    - title: Visible title of corpus
    - contents: List of book names this corpus contains
    """
    # Remove any existing version of this corpus
    cur.execute("""
        DELETE FROM corpus WHERE name = %(name)s;
    """, corpus)

    if corpus.get('carousel_image_path', None):
        with open(corpus['carousel_image_path'], 'rb') as f:
            corpus['carousel_image'] = f.read()
    else:
        corpus['carousel_image'] = None

    # Add main entry
    cur.execute("""
        INSERT INTO corpus (name, title, carousel_image, ordering)
             VALUES (%(name)s, %(title)s, %(carousel_image)s, %(ordering)s)
          RETURNING corpus_id
    """, corpus)
    (corpus_id,) = cur.fetchone()

    # Add links to books
    cur.execute("""
        INSERT INTO corpus_book (corpus_id, book_id)
             SELECT %(corpus_id)s corpus_id
                  , b.book_id
               FROM book b
              WHERE b.name IN %(book_names)s
    """, dict(
        corpus_id=corpus_id,
        book_names=tuple(corpus['contents'])
    ))
    if cur.rowcount != len(corpus['contents']):
        raise ValueError("Not all books in corpus exist in database %s" % corpus['contents'])
