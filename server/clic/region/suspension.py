"""
clic.region.suspension: Tag quote.suspension.* regions
******************************************************

We need paragraph/quote regions before we can do quote tagging::

    >>> from .chapter import tagger_chapter
    >>> from .metadata import tagger_metadata
    >>> from .quote import tagger_quote

quote.suspension regions
------------------------

A suspension is ``quote.nonquote`` (see :mod:`clic.region.quote`) region that...

* Has at least one word
* Does not start at a ``chapter.paragraph`` start.
* Does not contain the end of a ``chapter.sentence`` region.
* The first letter of the region is lower-case.

This implies that all suspensions are between 2 quote regions. If not, either...

* They are at the start of a chapter, thus the start of a paragraph. From ``ChiLit/stalky.txt``::

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

* They are at the end of a chapter, thus contain the end of a sentence. From ``ChiLit/daisy.txt``::

    >>> [x for x in run_tagger('''
    ... “Faithful in a little--” said Ethel. “I suppose all good people’s
    ... standard is always going higher.”
    ...
    ... “As they comprehend more of absolute perfection,” said Margaret.
    ...
    ...
    ... CHAPTER XV.
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.quote', 0, 24, None, '“Faithful in a little--”'),
     ('quote.nonquote', 25, 36, None, 'said Ethel.'),
     ('quote.suspension.short', 25, 36, None, 'said Ethel.'),
     ('quote.quote', 37, 99, None, '“I suppose all good ...lways going higher.”'),
     ('quote.quote', 101, 150, None, '“As they comprehend ...bsolute perfection,”'),
     ('quote.nonquote', 151, 165, None, 'said Margaret.')]

We do not consider how the preceding quote ends, only that the
``quote.nonquote`` region does not start with an upper case letter. Thus the
preceding quote can still end with exclamation mark, or other sentence-final
punctuation. From ``ChiLit/daisy.txt``::

    >>> [x for x in run_tagger('''
    ... “My dear Miss Flora!” began Miss Rich, adhering to her as they parted
    ... with the rest at the end of the street, “how am I to write to a
    ... principal? Am I to begin Reverend Sir, or My Lord, or is he Venerable,
    ... like an archdeacon? What is his name, and what am I to say?”
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.quote', 0, 21, None, '“My dear Miss Flora!”'),
     ('quote.nonquote', 22, 109, None, 'began Miss Rich, adh...e end of the street,'),
     ('quote.suspension.long', 22, 109, None, 'began Miss Rich, adh...e end of the street,'),
     ('quote.quote', 110, 265, None, '“how am I to write t...d what am I to say?”')]

...and...

    >>> [x for x in run_tagger('''
    ... “Oh, thank you!” and, “How she will like it!”
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.quote', 0, 16, None, '“Oh, thank you!”'),
     ('quote.nonquote', 17, 21, None, 'and,'),
     ('quote.suspension.short', 17, 21, None, 'and,'),
     ('quote.quote', 22, 45, None, '“How she will like it!”')]

Conversely, the following doesn't count as it starts with a capital Y. From
``ChiLit/daisy.txt``::

    >>> [x for x in run_tagger('''
    ... sorrowfully moralising and making excuses. “People in former times had
    ... not so high an estimate of pastoral duty--poor Mr. Ramsden had not much
    ... education--he was already old when better times came in--he might have
    ... done better in a less difficult parish with better laity to support him,
    ... etc.” Yet after all, he exclaimed with one of his impatient gestures,
    ... “Better have my Harry’s seventeen years than his sixty-seven!”
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.nonquote', 0, 42, None, 'sorrowfully moralisi... and making excuses.'),
     ('quote.quote', 43, 292, None, '“People in former ti...o support him,\\netc.”'),
     ('quote.nonquote', 293, 356, None, 'Yet after all, he ex... impatient gestures,'),
     ('quote.quote', 357, 419, None, '“Better have my Harr...an his sixty-seven!”')]

Due to the condition of starting with lower case, suspensions will not be
detected if they start with a name. The following do not count as suspensions.
From ``ChiLit/alice.txt``::

    >>> [x for x in run_tagger('''
    ... ‘No, please go on!’ Alice said very humbly; ‘I won’t interrupt again. I
    ... dare say there may be ONE.’
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.quote', 0, 19, None, '‘No, please go on!’'),
     ('quote.nonquote', 20, 43, None, 'Alice said very humbly;'),
     ('quote.quote', 44, 99, None, '‘I won’t interrupt a...y there may be ONE.’')]

    >>> [x for x in run_tagger('''
    ... ‘O Mouse, do you know the way out of this pool? I am very tired
    ... of swimming about here, O Mouse!’ (Alice thought this must be the right
    ... way of speaking to a mouse: she had never done such a thing before, but
    ... she remembered having seen in her brother’s Latin Grammar, ‘A mouse--of
    ... a mouse--to a mouse--a mouse--O mouse!’)
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.quote', 0, 97, None, '‘O Mouse, do you kno...bout here, O Mouse!’'),
     ('quote.nonquote', 98, 266, None, '(Alice thought this ...her’s Latin Grammar,'),
     ('quote.quote', 267, 319, None, '‘A mouse--of\\na mouse...--a mouse--O mouse!’'),
     ('quote.nonquote', 319, 320, None, ')')]

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

    Please clarify what happens with "suspensions" that do not contain any text, will they be dropped by the lower case rule (they should not be suspensions. but there aren't many of them and they're caused by special typesetting so we can live with them if need be).

But there has to be at least one word. Pure punctuation will not count as a
suspension. From ``ChiLit/daisy.txt``::

    >>> [x for x in run_tagger('''
    ... “I found her far better instructed than her appearance had led
    ... me to expect, and more truly impressed with the spirit of what she had
    ... learned than it has often been my lot to find children. She was perfect
    ... in the New Testament history”--(“Ah! that she was not, when she went
    ... away!”)--“and was in the habit of constantly attending church, and using
    ... morning and evening prayers.”
    ... '''.strip(), tagger_chapter, tagger_quote, tagger_quote_suspension) if x[0].startswith('quote.')]
    [('quote.quote', 0, 235, None, '“I found her far bet...w Testament history”'),
     ('quote.nonquote', 235, 238, None, '--('),
     ('quote.quote', 238, 281, None, '“Ah! that she was no...when she went\\naway!”'),
     ('quote.nonquote', 281, 284, None, ')--'),
     ('quote.quote', 284, 377, None, '“and was in the habi...nd evening prayers.”')]
"""
import re

import icu

from ..icuconfig import DEFAULT_LOCALE


INITIAL_ALPHANUMERIC_REGEX = re.compile(r'^(?:\W|_)*(.)')


def tagger_quote_suspension(book):
    """Add quote.suspension tags to (book)"""
    if len(book.get('quote.suspension.short', [])) > 0 or len(book.get('quote.suspension.long', [])) > 0:
        return  # Nothing to do

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
    s_i = 0
    paragraph_starts = set(r[0] for r in book['chapter.paragraph'])
    for containing_r in book['quote.nonquote']:
        if containing_r[0] in paragraph_starts:
            # Starts with a paragraph break, so not a suspension
            continue

        m = INITIAL_ALPHANUMERIC_REGEX.match(book['content'][containing_r[0]:containing_r[1]])
        if m and m.group(1).isupper():
            # First alphanumeric is an upper case character, ignore
            continue

        while cur_sent_b < containing_r[1]:  # while current sentence boundary is before end-of-region
            if cur_sent_b > containing_r[0]:  # If it's after the start-of-region also
                # There is a sentence boundary after the start of this region, ignore and move on
                break
            # Find the next end-of-sentence (NB: regions are end-exclusive, so go back one)
            s_i += 1
            if s_i >= len(book['chapter.sentence']):
                # Run out of sentences, move to end of book.
                cur_sent_b = len(book['content'])
            else:
                cur_sent_b = book['chapter.sentence'][s_i][1] - 1
        else:
            # Considered all potential sentence boundaries and none found, this is a suspension.
            word_count = count_words(*containing_r)
            if word_count >= 5:
                book['quote.suspension.long'].append(containing_r)
            elif word_count >= 1:
                book['quote.suspension.short'].append(containing_r)
