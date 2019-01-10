"""
clic.region.suspension: Tag quote.suspension.* regions
******************************************************

We need paragraph/quote regions before we can do quote tagging::

    >>> from .chapter import tagger_chapter
    >>> from .metadata import tagger_metadata
    >>> from .quote import tagger_quote

quote.suspension regions
------------------------

A suspension is defined as a ``quote.nonquote`` that is not bordered by the end or start
of a sentence (see :mod:`clic.region.chapter`).
If it is longer than 5 words, then it is a long suspension. For example::

    >>> [x for x in run_tagger('''
    ... “And on what evidence, Pip,” asked Mr. Jaggers, very coolly, as he
    ... paused with his handkerchief half way to his nose, “does Provis make this
    ... claim?”
    ...
    ... “He does not make it,” said I, “and has never made it, and has no knowledge
    ... or belief that his daughter is in existence.”
    ...
    ... ‘And this is Schloss Adlerstein?’ she exclaimed.
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.quote', 0, 28, None, '“And on what evidence, Pip,”'),
     ('quote.nonquote', 29, 117, None, 'asked Mr. Jaggers, v...alf way to his nose,'),
     ('quote.suspension.long', 29, 117, None, 'asked Mr. Jaggers, v...alf way to his nose,'),
     ('quote.quote', 118, 148, None, '“does Provis make this\\nclaim?”'),
     ('quote.quote', 150, 172, None, '“He does not make it,”'),
     ('quote.nonquote', 173, 180, None, 'said I,'),
     ('quote.suspension.short', 173, 180, None, 'said I,'),
     ('quote.quote', 181, 271, None, '“and has never made ...er is in existence.”'),
     ('quote.quote', 273, 306, None, '‘And this is Schloss Adlerstein?’'),
     ('quote.nonquote', 307, 321, None, 'she exclaimed.')]

This example doesn't count, since it starts with a sentence::

    >>> [x for x in run_tagger('''
    ... Little Benjamin said: "It spoils people's clothes to squeeze under a gate;
    ... the proper way to get in is to climb down a pear-tree."
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.nonquote', 0, 21, None, 'Little Benjamin said:'),
     ('quote.quote', 22, 130, None, '"It spoils people\\'s ...b down a pear-tree."')]

The start of a chapter should not count as a suspension either, as there is a
start-of-sentence at the start/ From ``ChiLit/stalky.txt``::

    >>> [x for x in run_tagger('''
    ... The black gown tore past like a thunder-storm, and in its wake, three
    ... abreast, arms linked, the Aladdin company rolled up the big corridor to
    ... prayers, singing with most innocent intention:
    ...
    ... CHAPTER 3. AN UNSAVORY INTERLUDE.
    ...
    ... It was a maiden aunt of Stalky who sent him both books, with the
    ... inscription, “To dearest Artie, on his sixteenth birthday;” it was
    ... McTurk who ordered their hypothecation.
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.') or x[0] == 'chapter.title']
    [('quote.nonquote', 0, 188, None, 'The black gown tore ... innocent intention:'),
     ('chapter.title', 190, 223, 1, 'CHAPTER 3. AN UNSAVORY INTERLUDE.'),
     ('quote.nonquote', 225, 302, None, 'It was a maiden aunt...ith the\\ninscription,'),
     ('quote.quote', 303, 349, None, '“To dearest Artie, o...sixteenth birthday;”'),
     ('quote.nonquote', 350, 396, None, 'it was\\nMcTurk who or...their hypothecation.')]
"""
import icu

from ..icuconfig import DEFAULT_LOCALE


def tagger_quote_suspension(book):
    """Add quote.suspension tags to (book)"""
    if len(book.get('quote.suspension.short', [])) > 0 or len(book.get('quote.suspension.long', [])) > 0:
        return  # Nothing to do

    # Iterator that iterates through the start and end of each sentence
    def sentence_breaks_fn():
        for r in book['chapter.sentence']:
            yield r[0]
            yield r[1]
    sentence_breaks = sentence_breaks_fn()

    # Create a word iterator for this book
    bi = icu.BreakIterator.createWordInstance(DEFAULT_LOCALE)
    bi.setText(book['content'])

    def count_words(f, t):
        out = 0
        bi.following(f - 1)
        for b in bi:
            if b > t:
                break
            if bi.getRuleStatus() > 0:
                out += 1
        return out

    cur_sent_b = -10  # i.e. a value we'll consider before-range
    book['quote.suspension.short'] = []
    book['quote.suspension.long'] = []
    for containing_r in book['quote.nonquote']:
        while cur_sent_b < containing_r[1] + 3:  # while current sentence boundary is before end-of-region
            if cur_sent_b > containing_r[0] - 3:  # If it's after the start-of-region also
                # There is a sentence boundary within this region, ignore and move on
                break
            cur_sent_b = next(sentence_breaks)
        else:
            # Considered all potential sentence boundaries and none found, this is a suspension.
            if count_words(*containing_r) < 5:
                book['quote.suspension.short'].append(containing_r)
            else:
                book['quote.suspension.long'].append(containing_r)
