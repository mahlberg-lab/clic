def get_corpus_structure(cdb):
    """
    Return a list of dicts containing:
    - id: corpus short name
    - title: corpus title
    - children: [{id: book id, title: book title, author: book author}, ...]
    """
    c = cdb.rdb_query("SELECT c.corpus_id, c.title, b.book_id, b.title, b.author FROM corpus c, book b WHERE b.corpus_id = c.corpus_id ORDER BY c.title, b.title")

    out = []
    for (c_id, c_title, b_id, b_title, b_author) in c:
        if len(out) == 0 or out[-1]['id'] != c_id:
            out.append(dict(id=c_id, title=c_title, children=[]))
        out[-1]['children'].append(dict(id=b_id, title=b_title, author=b_author))
    return out
