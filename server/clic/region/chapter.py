"""
Add chapter.* tags to regions.

Chapter tagging depends on metadata region tags::

    >>> from .metadata import tagger_metadata

chapter.title / chapter.text regions
------------------------------------

Any chapter conforming to the definition in corpora gets detected, and the text
afterwards will be marked as chapter.text::

    >>> run_tagger('''
    ... Initial text is the zero'th chapter.
    ...
    ... INTRODUCTION.
    ...
    ... The introduction has some chapter text.
    ... It's not very exciting.
    ...
    ... CHAPTER I. The first chapter
    ...
    ... The first chapter has some text.
    ...
    ... CHAPTER II. The second, empty, chapter
    ...
    ... CHAPTER III. The third, chapter
    ...
    ... ...has some text too, which goes to the very end.
    ... '''.strip(), tagger_metadata, tagger_chapter_title, tagger_chapter_text)
    [('chapter.text', 0, 36, 0, "Initial text is the zero'th chapter."),
     ('chapter.title', 38, 51, 1, 'INTRODUCTION.'),
     ('chapter.text', 53, 116, 1, 'The introduction has...s not very exciting.'),
     ('chapter.title', 118, 146, 2, 'CHAPTER I. The first chapter'),
     ('chapter.text', 148, 180, 2, 'The first chapter has some text.'),
     ('chapter.title', 182, 220, 3, 'CHAPTER II. The second, empty, chapter'),
     ('chapter.title', 222, 253, 4, 'CHAPTER III. The third, chapter'),
     ('chapter.text', 255, 304, 4, '...has some text too...oes to the very end.')]

We ignore any metadata if it's there::

    >>> run_tagger('''
    ... Fly Fishing
    ... J R Hartley
    ...
    ... Initial text is the zero'th chapter, but not including title.
    ...
    ... INTRODUCTION.
    ...
    ... The introduction has some chapter text.
    ... It's not very exciting.
    ... '''.strip(), tagger_metadata, tagger_chapter_title, tagger_chapter_text)
    [('metadata.title', 0, 11, None, 'Fly Fishing'),
     ('metadata.author', 12, 23, None, 'J R Hartley'),
     ('chapter.text', 25, 86, 0, 'Initial text is the ...not including title.'),
     ('chapter.title', 88, 101, 1, 'INTRODUCTION.'),
     ('chapter.text', 103, 166, 1, 'The introduction has...s not very exciting.')]

It's possible to not have any chapters too::

    >>> run_tagger('''
    ... Here is some text, without any preamble
    ... It's not very exciting.
    ... '''.strip(), tagger_metadata, tagger_chapter_title, tagger_chapter_text)
    [('chapter.text', 0, 63, 0, 'Here is some text, w...s not very exciting.')]

Paragraph / sentence counts reset at the start of the new chapter.

    >>> [x for x in run_tagger('''
    ... Initial text is the zero'th chapter. Second sentence.
    ...
    ... INTRODUCTION.
    ...
    ... First chapter, first sentence. Second sentence. Third sentence.
    ...
    ... Second paragraph, fourth sentence. Fifth!
    ...
    ... CHAPTER I. The first chapter
    ...
    ... First chapter, first sentence. Second sentence. Third.
    ...
    ... Second paragraph, fourth sentence. Fifth!
    ... '''.strip(), tagger_metadata, tagger_chapter) if x[0] in ['chapter.paragraph', 'chapter.sentence']]
    [('chapter.paragraph', 0, 53, 1, 'Initial text is the ...er. Second sentence.'),
     ('chapter.sentence', 0, 36, 1, "Initial text is the zero'th chapter."),
     ('chapter.sentence', 37, 53, 2, 'Second sentence.'),
     ('chapter.paragraph', 70, 133, 1, 'First chapter, first...nce. Third sentence.'),
     ('chapter.sentence', 70, 100, 1, 'First chapter, first sentence.'),
     ('chapter.sentence', 101, 117, 2, 'Second sentence.'),
     ('chapter.sentence', 118, 133, 3, 'Third sentence.'),
     ('chapter.paragraph', 135, 176, 2, 'Second paragraph, fo...rth sentence. Fifth!'),
     ('chapter.sentence', 135, 169, 4, 'Second paragraph, fourth sentence.'),
     ('chapter.sentence', 170, 176, 5, 'Fifth!'),
     ('chapter.paragraph', 208, 262, 1, 'First chapter, first...ond sentence. Third.'),
     ('chapter.sentence', 208, 238, 1, 'First chapter, first sentence.'),
     ('chapter.sentence', 239, 255, 2, 'Second sentence.'),
     ('chapter.sentence', 256, 262, 3, 'Third.'),
     ('chapter.paragraph', 264, 305, 2, 'Second paragraph, fo...rth sentence. Fifth!'),
     ('chapter.sentence', 264, 298, 4, 'Second paragraph, fourth sentence.'),
     ('chapter.sentence', 299, 305, 5, 'Fifth!')]

chapter.part regions
--------------------

Chapters can be interleaved with "PART x." or "BOOK x." headings, these will
marked a "chapter.part". They don't influence chapter counts, but aren't part
of chapter.text. For example::

    >>> [x for x in run_tagger('''
    ... Initial text is the zero'th chapter. Second sentence.
    ...
    ... BOOK 1.
    ...
    ... CHAPTER I. The first chapter in Book 1
    ...
    ... The text in chapter 1.
    ...
    ... CHAPTER II. The second chapter
    ...
    ... The text in chapter 2.
    ...
    ... BOOK 2.
    ...
    ... Some introductory text at start of the book.
    ...
    ... CHAPTER I. The first chapter in Book 2
    ...
    ... First chapter. Note that the chapter numbers carry on from previous book
    ... '''.strip(), tagger_metadata, tagger_chapter) if x[0] in ['chapter.part', 'chapter.title', 'chapter.text']]
    [('chapter.text', 0, 53, 0, 'Initial text is the ...er. Second sentence.'),
     ('chapter.part', 55, 62, 1, 'BOOK 1.'),
     ('chapter.title', 64, 102, 1, 'CHAPTER I. The first chapter in Book 1'),
     ('chapter.text', 104, 126, 1, 'The text in chapter 1.'),
     ('chapter.title', 128, 158, 2, 'CHAPTER II. The second chapter'),
     ('chapter.text', 160, 182, 2, 'The text in chapter 2.'),
     ('chapter.part', 184, 191, 2, 'BOOK 2.'),
     ('chapter.text', 193, 237, 2, 'Some introductory te...t start of the book.'),
     ('chapter.title', 239, 277, 3, 'CHAPTER I. The first chapter in Book 2'),
     ('chapter.text', 279, 351, 3, 'First chapter. Note ...n from previous book')]

chapter.paragraph / chapter.sentence regions
--------------------------------------------

Paragraph tagging occurs within chapter text, we split on "\n\n". Sentence
tagging occurs within paragraphs, and uses standard unicode sentence break
rules, apart from breaking at the end of lines::

    >>> run_tagger('''
    ... “Thou find’st it out, child?  Ay, ’tis worth all the feather-beds and\r
    ... pouncet-boxes in Ulm; is it not?  That accursed Italian fever never left
    ... me till I came up here.  A man can scarce draw breath in your foggy
    ... meadows below there.  Now then, here is the view open.  What think you of
    ... the Eagle’s Nest?”
    ...
    ... “And this is Schloss Adlerstein?” she exclaimed.
    ...
    ... “That is Schloss Adlerstein; and there shalt thou be in two hours’ time,
    ... unless the devil be more than usually busy, or thou mak’st a fool of
    ... thyself.  If so, not Satan himself could save thee.”
    ...
    ... '''.strip(), tagger_metadata, tagger_chapter)
    [('chapter.text', 0, 549, 0, '“Thou find’st it out...lf could save thee.”'),
     ('chapter.paragraph', 0, 303, 1, '“Thou find’st it out...f\\nthe Eagle’s Nest?”'),
     ('chapter.sentence', 0, 28, 1, '“Thou find’st it out, child?'),
     ('chapter.sentence', 30, 102, 2, 'Ay, ’tis worth all t...s in Ulm; is it not?'),
     ('chapter.sentence', 104, 166, 3, 'That accursed Italia...till I came up here.'),
     ('chapter.sentence', 168, 231, 4, 'A man can scarce dra...meadows below there.'),
     ('chapter.sentence', 233, 265, 5, 'Now then, here is the view open.'),
     ('chapter.sentence', 267, 303, 6, 'What think you of\\nthe Eagle’s Nest?”'),
     ('chapter.paragraph', 305, 353, 2, '“And this is Schloss...ein?” she exclaimed.'),
     ('chapter.sentence', 305, 338, 7, '“And this is Schloss Adlerstein?”'),
     ('chapter.sentence', 339, 353, 8, 'she exclaimed.'),
     ('chapter.paragraph', 355, 549, 3, '“That is Schloss Adl...lf could save thee.”'),
     ('chapter.sentence', 355, 505, 9, '“That is Schloss Adl...t a fool of\\nthyself.'),
     ('chapter.sentence', 507, 549, 10, 'If so, not Satan him...lf could save thee.”')]

By default, unicode sentence breaks would occur at the end of lines without any
punctuation. Instead, we ignore end of lines unless they would be a sentence
break anyway::

    >>> [x for x in run_tagger('''
    ... modest-looking little shop-window, containing a few newspapers, some
    ... Rather yellow packets of stationery, and two or three books of ballads.
    ... Above the door was painted in very small, dingy letters, the words,
    ... "James Oliver, News Agent."
    ... '''.strip(), tagger_metadata, tagger_chapter) if x[0] in ('chapter.paragraph', 'chapter.sentence')]
    [('chapter.paragraph', 0, 236, 1, 'modest-looking littl...Oliver, News Agent."'),
     ('chapter.sentence', 0, 140, 1, 'modest-looking littl...ee books of ballads.'),
     ('chapter.sentence', 141, 236, 2, 'Above the door was p...Oliver, News Agent."')]
"""
import re

import icu

from ..icuconfig import DEFAULT_LOCALE
from .utils import region_append_without_whitespace


PART_BREAK_REGEX = re.compile(
    '^' +
    '(PART|BOOK)' +
    ' ([0-9IVXLC]+)\.' +
    '.*', re.MULTILINE)

CHAPTER_BREAK_REGEX = re.compile(
    '^' +
    '(APPENDIX|INTRODUCTION|PREFACE|CHAPTER|CONCLUSION|PROLOGUE|PRELUDE|MORAL)' +
    '\s?' +
    '([0-9IVXLC]*)\.' +
    '.*', re.MULTILINE)

PARAGRAPH_BREAK_REGEX = re.compile(r'\n\n')


def tagger_chapter_part(book):
    """Add chapter.part tags to (book)"""
    if len(book.get('chapter.part', [])) > 0:
        return  # Nothing to do
    book['chapter.part'] = [
        m.span() + (i + 1,)
        for i, m in enumerate(re.finditer(PART_BREAK_REGEX, book['content']))
    ]


def tagger_chapter_title(book):
    """Add chapter.title tags to (book)"""
    if len(book.get('chapter.title', [])) > 0:
        return  # Nothing to do
    book['chapter.title'] = [
        m.span() + (i + 1,)
        for i, m in enumerate(re.finditer(CHAPTER_BREAK_REGEX, book['content']))
    ]


def tagger_chapter_text(book):
    """Add chapter.text tags to (book)"""
    if len(book.get('chapter.text', [])) > 0:
        return  # Nothing to do
    book['chapter.text'] = []

    # Gather anything together that shouldn't be part of a chapter, sort in document order
    headings = (book.get('metadata.title', []) + book.get('metadata.author', []) +
                book.get('chapter.part', []) + book.get('chapter.title', []) +
                [(len(book['content']), len(book['content']))])
    headings.sort(key=lambda r: (r[0], -r[1]))

    # Add everything outside headings to a chapter.text section, numbering with chapter counts
    last_b = 0
    chapter_num = 0
    for r in headings:
        region_append_without_whitespace(book, 'chapter.text', last_b, r[0], chapter_num)
        if r in book.get('chapter.title', []):
            # Text should have the same chapter number as it's title
            chapter_num = r[2]
        last_b = r[1]


def tagger_chapter_paragraph(book):
    """Add chapter.paragraph tags to (book)"""
    if len(book.get('chapter.paragraph', [])) > 0:
        return  # Nothing to do

    book['chapter.paragraph'] = []
    for containing_r in book['chapter.text']:
        last_b = containing_r[0]
        i = 1
        for m in PARAGRAPH_BREAK_REGEX.finditer(book['content'], containing_r[0], containing_r[1]):
            b = m.start()
            if region_append_without_whitespace(book, 'chapter.paragraph', last_b, b, i):
                i += 1
            last_b = b

        # Mark anything remaining as a paragraph too
        b = containing_r[1]
        region_append_without_whitespace(book, 'chapter.paragraph', last_b, b, i)


def tagger_chapter_sentence(book):
    """Add chapter.sentence tags to (book)"""
    if len(book.get('chapter.sentence', [])) > 0:
        return  # Nothing to do

    # Create a sentence iterator for this book
    bi = icu.BreakIterator.createSentenceInstance(DEFAULT_LOCALE)
    bi.setText(re.sub(r'\n(?!\n)', ' ', book['content']))  # Turn single newlines into spaces, so ICU ignores them.

    book['chapter.sentence'] = []
    for containing_r in book['chapter.text']:
        last_b = containing_r[0]
        i = 1

        # Move iterator to break that starts chapter (or before), next break will be within
        bi.preceding(containing_r[0] + 1)
        for b in bi:
            if b > containing_r[1]:
                # Outside the chapter now, so stop
                break
            if region_append_without_whitespace(book, 'chapter.sentence', last_b, b, i):
                i += 1
            last_b = b

        # Mark anything remaining as a sentence too
        b = containing_r[1]
        region_append_without_whitespace(book, 'chapter.sentence', last_b, b, i)


def tagger_chapter(book):
    """Add chapter.* tags to (book)"""
    tagger_chapter_part(book)
    tagger_chapter_title(book)
    tagger_chapter_text(book)
    tagger_chapter_paragraph(book)
    tagger_chapter_sentence(book)
