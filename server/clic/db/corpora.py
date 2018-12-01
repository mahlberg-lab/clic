"""
clic.db.corpora: Resolve corpora lists
**************************************

corpora_to_book_ids
===================

There are various ways we can specify which books to search in the corpora
parameter. They are specified below.

Make a very cut-down library of books, with the word "the" so we can search for
all of them::

    >>> from clic.db.corpus import put_corpus
    >>> db_cur = test_database(
    ... alice='''
    ... Alice’s Adventures in Wonderland
    ... Lewis Carroll
    ...
    ... the
    ... '''.strip(),
    ...
    ... willows='''
    ... The Wind in the Willows
    ... Kenneth Grahame
    ...
    ... the
    ... '''.strip(),
    ...
    ... sense='''
    ... Sense and Sensibility
    ... Jane Austen
    ...
    ... the
    ... '''.strip(),
    ...
    ... northanger='''
    ... Northanger Abbey
    ... Jane Austen
    ...
    ... the
    ... '''.strip(),
    ...
    ... gulliver='''
    ... Gulliver's Travels
    ... Jonathan Swift
    ...
    ... the
    ... '''.strip())
    >>> put_corpus(db_cur, dict(name='ChiLit', contents=['alice', 'willows'], title='', ordering=1))
    >>> put_corpus(db_cur, dict(name='ArTs', contents=['sense', 'northanger', 'gulliver'], title='', ordering=2))

We will use concordance for these examples, but the choice shouldn't matter::

    >>> from ..concordance import concordance

book name
---------

We can use book names directly::

    >>> just_metadata(concordance(db_cur, ['alice', 'willows'], q=["the"], metadata=['book_titles']))
    {'book_titles':
      {'alice': ['Alice’s Adventures in Wonderland', 'Lewis Carroll'],
       'willows': ['The Wind in the Willows', 'Kenneth Grahame']}}

author
------

We can use the author name to get any books by a given author::

    >>> just_metadata(concordance(db_cur, ['author:Jane Austen'], q=["the"], metadata=['book_titles']))
    {'book_titles':
      {'northanger': ['Northanger Abbey', 'Jane Austen'],
       'sense': ['Sense and Sensibility', 'Jane Austen']}}

corpus name
-----------

We can use the corpus name::

    >>> just_metadata(concordance(db_cur, ['corpus:ChiLit'], q=["the"], metadata=['book_titles']))
    {'book_titles':
      {'alice': ['Alice’s Adventures in Wonderland', 'Lewis Carroll'],
       'willows': ['The Wind in the Willows', 'Kenneth Grahame']}}

old names
---------

There are some old names that whilst are deprecated, should still work::

    >>> just_metadata(concordance(db_cur, ['Other'], q=["the"], metadata=['book_titles']))
    {'book_titles':
      {'gulliver': ["Gulliver's Travels", 'Jonathan Swift'],
       'northanger': ['Northanger Abbey', 'Jane Austen'],
       'sense': ['Sense and Sensibility', 'Jane Austen']}}
"""
OLD_ALIASES = dict(
    dickens=['corpus:DNov'],
    ntc=['corpus:19C'],
    ChiLit=['corpus:ChiLit'],
    Other=['corpus:ArTs'],
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
               WHERE bm.rclass_id = (SELECT rclass_id FROM rclass WHERE name = 'metadata.author')
                 AND bm.content = %(author)s;
            """, dict(
                author=c[len('author:'):],
            ))
            out.extend([r[0] for r in cur])
        else:
            # Assume book name
            cur.execute("SELECT book_id FROM book WHERE name = %s", (c,))
            out.extend([r[0] for r in cur])
    return out
