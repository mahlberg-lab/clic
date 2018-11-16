"""
get_book_metadata
=================

For each query type that supports it, a ``metadata`` option can be provided to
add extra information about each book mentioned in the query.

These are the books we use for the below::

    >>> db_cur = test_database(
    ... alice='''
    ... Alice’s Adventures in Wonderland
    ... Lewis Carroll
    ...
    ... CHAPTER I. Down the Rabbit-Hole
    ...
    ... ‘Well!’ thought Alice to herself, ‘after such a fall as this, I shall
    ... think nothing of tumbling down stairs! How brave they’ll all think me at
    ... home! Why, I wouldn’t say anything about it, even if I fell off the top
    ... of the house!’ (Which was very likely true.)
    ...
    ... ‘I beg your pardon,’ said Alice very humbly: ‘you had got to the fifth
    ... bend, I think?’
    ...
    ... CHAPTER II. The Pool of Tears
    ...
    ... ‘I had NOT!’ cried the Mouse, sharply and very angrily.
    ... '''.strip(),
    ...
    ... willows='''
    ... The Wind in the Willows
    ... Kenneth Grahame
    ...
    ... CHAPTER I. THE RIVER BANK
    ...
    ... ‘Hold up!’ said an elderly rabbit at the gap. ‘Sixpence for the
    ... privilege of passing by the private road!’
    ...
    ... CHAPTER IV. MR. BADGER
    ...
    ... ‘Thought I should find you here all right,’ said the Otter cheerfully.
    ... ‘They were all in a great state of alarm along River Bank when I arrived
    ... this morning.’
    ... '''.strip())

We will use concordance for these examples, but the choice shouldn't matter::

    >>> from ..concordance import concordance
    >>> from ..subset import subset

book_titles
-----------

Return title/author for each book::

    >>> just_metadata(concordance(db_cur, ['alice', 'willows'], q=["the"], metadata=['book_titles']))
    {'book_titles':
      {'alice': ['Alice’s Adventures in Wonderland', 'Lewis Carroll'],
       'willows': ['The Wind in the Willows', 'Kenneth Grahame']}}

chapter_start
-------------

Return the position of the start of each chapter, and "_end" (of the book)::

    >>> just_metadata(concordance(db_cur, ['alice', 'willows'], q=["the"], metadata=['chapter_start']))
    {'chapter_start':
      {'alice': {1: 81, 2: 461, '_end': 516},
       'willows': {1: 68, 2: 200, '_end': 358}}}

word_count_chapter
------------------

Return the word count before the start of each chapter, and at the end of book with "_end"::

    >>> just_metadata(concordance(db_cur, ['alice', 'willows'], q=["the"], metadata=['word_count_chapter']))
    {'word_count_chapter':
      {'alice': {1: 0, 2: 66, '_end': 76},
      'willows': {1: 0, 2: 19, '_end': 48}}}

word_count_quote
----------------

Return the word count in quotes (or any other subset)::

    >>> just_metadata(concordance(db_cur, ['alice', 'willows'], q=["the"],
    ...     metadata=['word_count_quote', 'word_count_nonquote']))
    {'word_count_nonquote': {'alice': 20, 'willows': 11},
     'word_count_quote': {'alice': 56, 'willows': 37}}
"""
from clic.db.lookup import rclass_id_lookup, api_subset_lookup


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
