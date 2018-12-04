"""
clic.region.quote: Tag quote.* regions
**************************************

We need paragraph regions before we can do quote tagging::

    >>> from .chapter import tagger_chapter
    >>> from .metadata import tagger_metadata

quote.quote / quote.nonquote regions
------------------------------------

Quotes are discovered by parsing text using :mod:`clic.tokenizer` word boundary
rules. Open quotes are found when the text between any 2 word boundaries
matches one of our list of quote marks, and then a quote is formed when the
corresponding close quote mark is found::

    >>> [x for x in run_tagger('''
    ... “Thou find’st it out, child?  Ay, ’tis worth all the feather-beds and\r
    ... pouncet-boxes in Ulm; is it not?  That accursed Italian fever never left
    ... me till I came up here.  A man can scarce draw breath in your foggy
    ... meadows below there.  Now then, ‘here is the view open.’  What think you of
    ... the Eagle’s Nest?”
    ...
    ... ‘And this is Schloss Adlerstein?’ she exclaimed.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 305, None, '“Thou find’st it out...f\\nthe Eagle’s Nest?”'),
     ('quote.quote', 307, 340, None, '‘And this is Schloss Adlerstein?’'),
     ('quote.nonquote', 341, 355, None, 'she exclaimed.')]

In the all examples, the columns are:

1. Region class/type ('rclass'): e.g. 'quote.quote'
2. Start position, in characters through the text file: e.g. '0'
3. End position, in characters through the text file: e.g. '305'
4. Value, e.g. chapter number, paragraph-in-chapter number. As we don't number quotes and non-quotes, this will always say 'None' for these region classes.
5. A preview of the text that the region applies to, shortened if it's longer than 40 characters, purely for illustration.


Quotes should have one of ``,?.!-;_`` before the end quote, or ``--`` after::

    >>> [x for x in run_tagger('''
    ... "That," he said, "is a 'veritable banquet'."
    ...
    ... "Because"--"because father and mamma have to go away," I was going to say
    ...
    ... "Here's luck," "A fair wind," and "Billy Bones his fancy," were very neatly
    ... and clearly executed on the forearm.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 7, None, '"That,"'),
     ('quote.nonquote', 8, 16, None, 'he said,'),
     ('quote.quote', 17, 44, None, '"is a \\'veritable banquet\\'."'),
     ('quote.quote', 46, 55, None, '"Because"'),
     ('quote.nonquote', 55, 57, None, '--'),
     ('quote.quote', 57, 100, None, '"because father and ...ma have to go away,"'),
     ('quote.nonquote', 101, 119, None, 'I was going to say'),
     ('quote.quote', 121, 135, None, '"Here\\'s luck,"'),
     ('quote.quote', 136, 150, None, '"A fair wind,"'),
     ('quote.nonquote', 151, 154, None, 'and'),
     ('quote.quote', 155, 179, None, '"Billy Bones his fancy,"'),
     ('quote.nonquote', 180, 233, None, 'were very neatly\\nand...uted on the forearm.')]

...or be at least 5 words long, when using double quote marks::

    >>> [x for x in run_tagger('''
    ... The "exotic camels" were actually dromedaries.
    ... "Four words not quote" "Five words is a quote"
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.nonquote', 0, 69, None, 'The "exotic camels" ...our words not quote"'),
     ('quote.quote', 70, 93, None, '"Five words is a quote"')]

Quotes have to have one of the punctuation marks when single quotes are used,
as false-positives are too easy, e.g. ChiLit/moonfleet.txt::

    >>> [x for x in run_tagger('''
    ... laggard; though 'twas hard enough for men to walk where the mud was over
    ... the horses' fetlocks.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.nonquote', 0, 94, None, "laggard; though 'twa...he horses' fetlocks.")]

...or Chilit/alone.txt::

    >>> [x for x in run_tagger('''
    ... "Ah, it's not bad in the summer," said Tony, more earnestly than before:
    ... "and I could find for the little 'un easy enough. I sleep anywhere, in
    ... Covent Garden sometimes, and the parks--anywhere as the p'lice 'ill let
    ... me alone. You won't go to give her up to them p'lice, will you now, and
    ... she so pretty?"
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 33, None, '"Ah, it\\'s not bad in the summer,"'),
     ('quote.nonquote', 34, 72, None, 'said Tony, more earnestly than before:'),
     ('quote.quote', 73, 303, None, '"and I could find fo... and\\nshe so pretty?"')]

We only demand one of the types of punctuation, so quotes can start mid-sentence, e.g. ChiLit/alice.txt::

    >>> [x for x in run_tagger('''
    ... It was the White Rabbit, trotting slowly back again, and looking
    ... anxiously about as it went, as if it had lost something; and she heard
    ... it muttering to itself ‘The Duchess! The Duchess! Oh my dear paws! Oh
    ... my fur and whiskers! She’ll get me executed, as sure as ferrets are
    ... ferrets! Where CAN I have dropped them, I wonder?’ Alice guessed
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.nonquote', 0, 158, None, 'It was the White Rab... muttering to itself'),
     ('quote.quote', 159, 324, None, '‘The Duchess! The Du...ped them, I wonder?’'),
     ('quote.nonquote', 325, 338, None, 'Alice guessed')]

Extended quotes can run on across paragraphs, with an initial quote mark or indent to
indicate continuation. We combine these into one quote::

    >>> [x for x in run_tagger('''
    ... “Oh, that’s not all that complicated,” J.R. answered. “If you closed
    ... quotes at the end of every paragraph, then you would need to reidentify the
    ... speaker with every subsequent paragraph.
    ...
    ... “Say a narrative was describing two or three people engaged in a lengthy
    ... conversation. If you closed the quotation marks in the previous paragraph,
    ... reader knows that the previous speaker is still the one talking.”
    ...
    ... “Oh, that makes sense. Thanks!”
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 38, None, '“Oh, that’s not all that complicated,”'),
     ('quote.nonquote', 39, 53, None, 'J.R. answered.'),
     ('quote.quote', 54, 400, None, '“If you closed\\nquote...ll the one talking.”'),
     ('quote.quote', 402, 433, None, '“Oh, that makes sense. Thanks!”')]

Indents are also valid ways of continuing a quote, for example from ChiLit/overtheway.txt::

    >>> [x for x in run_tagger('''
    ... "Aunt Harriet was introduced as 'My daughter Harriet,' and made a
    ... stiff curtsey as Mrs. Moss smiled, and nodded, and bade her 'sit down,
    ... my dear.' Throughout the whole interview she seemed to be looked upon
    ... by both ladies as a child, and played the part so well, sitting prim
    ... and silent on her chair, that I could hardly help humming as I looked
    ... at her:
    ...
    ...     'Hold up your head,
    ...     Turn out your toes,
    ...     Speak when you're spoken to,
    ...     Mend your clothes.'
    ...
    ... "I was introduced, too, as 'a grandchild,' made a curtsey the shadow of
    ... Aunt Harriet's, received a nod, the shadow of that bestowed upon her,
    ... and got out of the way as soon as I could, behind my aunt's chair,
    ... where, coming unexpectedly upon three fat pug-dogs on a mat, I sat
    ... down among them and felt quite at home."
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 777, None, '"Aunt Harriet was in...felt quite at home."')]

Extended quotes also work without curly quotes, example from ChiLit/water.txt::

    >>> [x for x in run_tagger('''
    ... "And I am very ugly.  I am the ugliest fairy in the world; and I
    ... going to do.  It will be a very good warning for him to begin with,
    ... before he goes to school.
    ...
    ... "Now, Tom, every Friday I come down here and call up all who have
    ... ill-used little children and serve them as they served the
    ... children."
    ...
    ... And at that Tom was frightened, and crept under a stone
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.quote', 0, 295, None, '"And I am very ugly....erved the\\nchildren."'),
     ('quote.nonquote', 297, 352, None, 'And at that Tom was ... crept under a stone')]

Extended quotes only carry on when a paragraph starts with a quote-mark. Erroneous quotes
in paragraphs shouldn't result in quotes running on. E.g. in the first paragraph
of the following example from ChiLit/moonfleet.txt, there's a ``'twixt``, 
which as this isn't in our whitelist, could be the start of a quote. 
There's no end-quote mark in the paragraph (the 'tis is in our whitelist), 
so either this is an extended quote or an apostrophe that should be ignored.
Since the second paragraph doesn't start with a quote mark or is indented, 
it's something to be ignored, so we make sure we ignore it.::

    >>> [x for x in run_tagger('''
    ... turning the
    ... space 'twixt ship and shore into a boiling caldron: a minute later 'twas
    ... all sucked back again with a roar, and we jumped.
    ...
    ... I fell on hands and feet where the water was a yard deep under the ship,
    ... crash and thunder of the returning wave we were but a fathom distant
    ... from the rope. 'Take heart, lad,' he cried; ''tis now or never,' and as
    ... the water reached our breasts gave me a fierce shove forward with his
    ... hands. There was a roar of water in my ears, with a great shouting of
    ... the men upon the beach, and then I caught the rope.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0] in set(('quote.quote', 'quote.nonquote'))]
    [('quote.nonquote', 0, 292, None, "turning the\\nspace 't...stant\\nfrom the rope."),
     ('quote.quote', 293, 311, None, "'Take heart, lad,'"),
     ('quote.nonquote', 312, 321, None, 'he cried;'),
     ('quote.quote', 322, 342, None, "''tis now or never,'"),
     ('quote.nonquote', 343, 541, None, 'and as\\nthe water rea...n I caught the rope.')]

Non-quote regions don't run outside chapters, so Titles aren't part of them::

    >>> [x for x in run_tagger('''
    ... The Wind in the Willows
    ... Kenneth Grahame
    ...
    ... CHAPTER I. THE RIVER BANK
    ...
    ... The Mole had been working very hard all the morning, spring-cleaning.
    ... ‘Hold up!’ said an elderly rabbit at the gap. ‘Sixpence for the
    ... privilege of passing by the private road!’
    ...
    ... CHAPTER IV. MR. BADGER
    ...
    ... ‘Thought I should find you here all right,’ said the Otter cheerfully.
    ...
    ... ‘They were all in a great state of alarm along River Bank when I arrived
    ... this morning.’
    ... '''.strip(), tagger_metadata, tagger_chapter, tagger_quote) if x[0] in set(('metadata.title', 'metadata.author', 'quote.quote', 'quote.nonquote'))]
    [('metadata.title', 0, 23, None, 'The Wind in the Willows'),
     ('metadata.author', 24, 39, None, 'Kenneth Grahame'),
     ('quote.nonquote', 68, 137, None, 'The Mole had been wo...ng, spring-cleaning.'),
     ('quote.quote', 138, 148, None, '‘Hold up!’'),
     ('quote.nonquote', 149, 183, None, 'said an elderly rabbit at the gap.'),
     ('quote.quote', 184, 244, None, '‘Sixpence for the\\npr...y the private road!’'),
     ('quote.quote', 270, 313, None, '‘Thought I should fi...you here all right,’'),
     ('quote.nonquote', 314, 340, None, 'said the Otter cheerfully.'),
     ('quote.quote', 342, 429, None, '‘They were all in a ...rived\\nthis morning.’')]

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
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0].startswith('quote.')]
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
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0].startswith('quote.')]
    [('quote.nonquote', 0, 21, None, 'Little Benjamin said:'),
     ('quote.quote', 22, 130, None, '"It spoils people\\'s ...b down a pear-tree."')]

quote.embedded regions
----------------------

A ``quote.embedded`` region follows the same rules as regular quotes, but inside a quote.

For example, from ChiLit/alice.txt::

    >>> [x for x in run_tagger('''
    ... ‘I thought you did,’ said the Mouse. ‘--I proceed. “Edwin and Morcar,
    ... the earls of Mercia and Northumbria, declared for him: and even Stigand,
    ... the patriotic archbishop of Canterbury, found it advisable--”’
    ...
    ... ‘Found WHAT?’ said the Duck.
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0].startswith('quote.')]
    [('quote.quote', 0, 20, None, '‘I thought you did,’'),
     ('quote.nonquote', 21, 36, None, 'said the Mouse.'),
     ('quote.quote', 37, 205, None, '‘--I proceed. “Edwin...und it advisable--”’'),
     ('quote.embedded', 51, 204, None, '“Edwin and Morcar,\\nt...ound it advisable--”'),
     ('quote.quote', 207, 220, None, '‘Found WHAT?’'),
     ('quote.nonquote', 221, 235, None, 'said the Duck.')]

Embedded quotes can also be found in multi-paragraph quotes, example from ChiLit/overtheway.txt::

    >>> [x for x in run_tagger('''
    ... "'Poor man! Did he ever marry?'
    ...
    ... "'Yes, and very happily--a charming woman. But the strange part of the
    ... story is, that he came quite unexpectedly into a large property that
    ... was in his family.'
    ...
    ... "'Did he? Then he would have been as good a match as most of her
    ... admirers?'
    ...
    ... "'Better. It was a fine estate. Poor Anastatia!'
    ...
    ... "'Serve her right,' said my aunt, shortly."
    ... '''.strip(), tagger_chapter, tagger_quote) if x[0].startswith('quote.')]
    [('quote.quote', 0, 364, None, '"\\'Poor man! Did he e...d my aunt, shortly."'),
     ('quote.embedded', 1, 31, None, "'Poor man! Did he ever marry?'"),
     ('quote.embedded', 34, 192, None, "'Yes, and very happi...\\nwas in his family.'"),
     ('quote.embedded', 195, 269, None, "'Did he? Then he wou...st of her\\nadmirers?'"),
     ('quote.embedded', 272, 319, None, "'Better. It was a fi...te. Poor Anastatia!'"),
     ('quote.embedded', 322, 340, None, "'Serve her right,'")]

.. http://unicode.org/reports/tr29/#Word_Boundaries
"""
import re

import icu

from ..icuconfig import DEFAULT_LOCALE
from ..tokenizer import word_boundary_type
from .utils import region_append_without_whitespace, regions_invert


QUOTES = {
    '“': '”',  # English double.
    '‘': '’',  # English Single.
    '"': '"',  # Double universal.
    "'": "'",  # Single universal.
}


def is_quote(s, q_start, q_end, wc):
    """Is this pair of quote-marks a valid quote, or "other construct" that should be ignored?"""
    # Quotes should have one of...

    # ...five or more words (for double quotes)
    if wc >= 5 and s[q_start] not in set(("’", "'")):
        return True
    # ... select punctuation before the quote
    if re.search(r'(?:\-\-|\(|,|:|;)\s*$', s[q_start - 4: q_start]):
        return True
    # ... select punctuation at the start
    if re.search(r'^\s*(?:\-\-)', s[q_start + 1: q_start + 6]):
        return True
    # ... select punctuation before the end
    if re.search(r'--\s*$|[,?.!-;_]$', s[q_end - 5:q_end - 1]):
        return True
    # ... select punctuation after the quote
    if re.search(r'^\s*--', s[q_end:q_end + 5]):
        return True
    return False


def tagger_quote_quote(book):
    """Add quote.quote tags to (book)"""
    if len(book.get('quote.quote', [])) > 0:
        return  # Nothing to do

    # Create a word iterator for this book
    bi = icu.BreakIterator.createWordInstance(DEFAULT_LOCALE)
    bi.setText(book['content'])

    book['quote.quote'] = []
    book['quote.embedded'] = []
    open_quote = None  # NB: Don't reset last-open-quote on each paragraph
    embedded_quote = None
    word_count = 0
    for containing_r in book['chapter.paragraph']:
        last_b = containing_r[0]

        if open_quote and not(book['content'][containing_r[0]:containing_r[0] + 1] in QUOTES or book['content'][containing_r[0] - 3:containing_r[0]] == '   '):
            # Continuing an open_quote from a previous paragarph, but paragraph didn't start with a quote marker or indent, ditch.
            open_quote = None

        # Get all word breaks after containing_r[0]
        bi.following(containing_r[0] - 1)
        for b in bi:
            if b > containing_r[1]:
                # Outside the chapter now, so stop. Leave any open quotes still open, assume any embedded quotes broken
                embedded_quote = None
                break
            word = book['content'][last_b:b]

            if word_boundary_type(book['content'], bi, last_b):
                # Text up to this boundary is "wordy", this includes our own extras, such as:
                # * Posessives, "3 days' work".
                # * Abbreviations, "'twas a dark and stormy night"
                # ...increase our word count and ignore these characters for quote-finding purposes.
                word_count += 1  # NB: Ideally shouldn't count over-the-top as 5, but too much of an edge case

            elif embedded_quote and word == embedded_quote[0]:
                # Found the closing quote for an embedded quote
                if is_quote(book['content'], embedded_quote[1], b, word_count - embedded_quote[2]):
                    book['quote.embedded'].append((embedded_quote[1], b))
                embedded_quote = None  # Clear open-quote regardless, we matched a pair of scare-quotes

            elif open_quote and last_b == containing_r[0]:
                # Quote still open from previous paragraph, ignore it and move on
                pass

            elif open_quote and word == open_quote[0]:
                # Found the closing quote we were looking for
                if is_quote(book['content'], open_quote[1], b, word_count - open_quote[2]):
                    book['quote.quote'].append((open_quote[1], b))
                    if embedded_quote:
                        # Ditch any still-open embedded quote
                        embedded_quote = None
                open_quote = None  # Clear open-quote regardless, we matched a pair of scare-quotes

            elif word in QUOTES:
                if open_quote and QUOTES[word] != open_quote[0]:
                    # An open-quote using a different marker within the quote, it's an embedded quote
                    embedded_quote = (QUOTES[word], last_b, word_count)
                else:
                    # Not in an open quote and found one
                    open_quote = (QUOTES[word], last_b, word_count)
            last_b = b


def tagger_quote_nonquote(book):
    """Add quote.nonquote tags to (book)"""
    if len(book.get('quote.nonquote', [])) > 0:
        return  # Nothing to do

    book['quote.nonquote'] = []
    # Combine quotes and everything not in a chapter
    quotes_and_nonchaps = book['quote.quote'][:]
    quotes_and_nonchaps.extend(regions_invert(book['chapter.text'], len(book['content'])))
    quotes_and_nonchaps.sort(key=lambda r: (r[0], -r[1]))

    # Non-quotes are the opposite of this
    for last_b, b in regions_invert(quotes_and_nonchaps, len(book['content'])):
        region_append_without_whitespace(book, 'quote.nonquote', last_b, b)


def tagger_quote_suspension(book):
    """Add quote.suspension tags to (book)"""
    if len(book.get('quote.suspension.short', [])) > 0 or len(book.get('quote.suspension.long', [])) > 0:
        return  # Nothing to do

    # Iterator that iterates through...
    # (a) The start of the first sentence
    # (b) The end of all sentences (including the first)
    # All other sentence-starts should be just after a sentence-end, so no point
    # considering
    def sentence_breaks_fn():
        if len(book['chapter.sentence']) > 0:
            yield book['chapter.sentence'][0][0]
        for r in book['chapter.sentence']:
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


def tagger_quote(book):
    """
    Add quote.* tags to regions
    """
    tagger_quote_quote(book)
    tagger_quote_nonquote(book)
    tagger_quote_suspension(book)
