'''
clic.db.corpora: Get/put corpora dicts to DB
********************************************
'''


def put_corpus(cur, corpus):
    """
    Add a corpus (i.e. a set of books) object to the database.

    A corpus object is a dict containing
    - name: Short name of corpus
    - title: Visible title of corpus
    - carousel_image_path: Filename to use for carousel image
    - ordering: Ordering of corpus entries in DB
    - example_url: An example CLiC URL to use in the carousel. Hostname will be stripped
    """
    # Replace image path with image content
    if corpus.get('carousel_image_path', None):
        with open(corpus['carousel_image_path'], 'rb') as f:
            corpus['carousel_image'] = f.read()
    else:
        corpus['carousel_image'] = None

    if corpus.get('example_url', None):
        corpus["example_url"] = corpus["example_url"].replace("https://clic-fiction.com/", "/")
    else:
        corpus["example_url"] = None

    # Insert, or update existing entry with matching name
    cur.execute("""
        INSERT INTO corpus (name, title, carousel_image, ordering, example_url)
             VALUES (%(name)s, %(title)s, %(carousel_image)s, %(ordering)s, %(example_url)s)
        ON CONFLICT (name) DO UPDATE
                SET title = EXCLUDED.title
                  , carousel_image = EXCLUDED.carousel_image
                  , ordering = EXCLUDED.ordering
                  , example_url = EXCLUDED.example_url
          RETURNING corpus_id
    """, corpus)
    (corpus_id,) = cur.fetchone()

    for b in corpus.get("contents", []):
        add_book_to_corpus(cur, corpus, dict(name=b))


def add_book_to_corpus(cur, corpus, book):
    """
    Add a book to a corpus (i.e. a set of books) in the database.

    A corpus object is a dict containing
    - name: Short name of corpus

    A book object is a dict containing
    - name: The shortname of the book
    """
    # Find corpus & book ID
    cur.execute("""
        SELECT corpus_id
          FROM corpus
         WHERE name = %(name)s
    """, dict(name=corpus['name']))
    (corpus_id,) = cur.fetchone()
    cur.execute("""
        SELECT book_id
          FROM book
         WHERE name = %(name)s
    """, dict(name=book['name']))
    (book_id,) = cur.fetchone()

    # Add link, ignore if already present
    cur.execute("""
        INSERT INTO corpus_book (corpus_id, book_id)
             VALUES (%(corpus_id)s, %(book_id)s)
        ON CONFLICT (corpus_id, book_id) DO NOTHING
    """, dict(
        corpus_id=corpus_id,
        book_id=book_id,
    ))
