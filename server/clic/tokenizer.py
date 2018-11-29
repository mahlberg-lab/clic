"""Tokenizer
************

This module provides the core tokenisation used in CLiC, used both when parsing
incoming texts and when parsing concordance queries

Method
------

To extract tokens, we use Unicode text segmentation as described in [UAX29]_,
using the implementation in the [ICU]_ library and standard rules for en_GB, and
then apply our own additions (see later).

Please read the document for a full description of ICU word boundaries, however
as a quick example the following phrase::

    The quick (“brown”) fox can’t jump 32.3 feet in-the-air, right?

...would have boundaries at every point marked with a ``|``::

    The| |quick| |(||“|brown|”|)| |fox| |can’t| |jump| |32.3| |feet| |in|-|the|-|air|,| |right|?|

We consider a boundary mark to be a word-boundary if...

* The type of the boundary according to ICU is at the end of a word (e.g. after ``jump``) or the end of a number (e.g. after ``32.3``).
* It is after a hyphen character surrounded by alpha-numeric characters, e.g. after all hyphens in ``|in|-|the|-|air|``.
* It is after an apostrophe preceded with s, e.g. after the ``'`` in ``3| |days|'| |work|``.
* It is after an apostrophe followed by one of a whitelist of words (see :const:`~INITIAL_ABBREVIATIONS`),
  e.g. after the ``'`` in ``'|tis| nothing|``.

Note that these additional rules are because ICU does not handle apostrophes on
the outside of words, nor hyphenated-words.

...so if we mark word boundaries in the example above with ``‖``::

    The‖ |quick‖ |(||“|brown‖”|)| |fox‖ |can’t‖ |jump‖ |32.3‖ |feet‖ |in‖-‖the‖-‖air‖,| |right‖?|

Tokens are then extracted by combining all text before adjacent word-boundaries, e.g.:

* ``‖ |feet‖`` becomes the token ``feet``.
* ``‖ |in‖-‖the‖-‖air‖,|`` becomes the token ``in-the-air``

Tokens are then normalised into types by:-

* Lower-casing, ``The`` -> ``the``.
* Normalising any non-ascii characters with [UNIDECODE]_, e.g.

  * ``can’t`` -> ``can't``.
  * ``café`` -> ``cafe``.

* Removing any surrounding underscores, e.g. ``_connoisseur_`` -> ``connoisseur``.

Queries for concordance searches are also turned into a list of types by this
module. In this case we consider ``*`` as being part of a token for wildcard
searches. See later examples for more information.

Examples / edge cases
---------------------

A type is lower-case, ASCII-representable term, and "fancy" apostrophes are normalised::

    >>> [x[0] for x in types_from_string('''
    ...     I am a café cat, don’t you k'now.
    ... ''')]
    ['i', 'am', 'a', 'cafe', 'cat', "don't", 'you', "k'now"]

Numbers are types too::

    >>> [x[0] for x in types_from_string('''
    ...     Just my $0.02, but we're 12 minutes late.
    ... ''')]
    ['just', 'my', '0.02', 'but', "we're", '12', 'minutes', 'late']

All surrounding punctuation is filtered out::

    >>> [x[0] for x in types_from_string('''
    ...     "I am a cat", they said, "hear me **roar**!".
    ...
    ...     "...or at least mew".
    ... ''')]
    ['i', 'am', 'a', 'cat', 'they', 'said', 'hear', 'me', 'roar',
     'or', 'at', 'least', 'mew']

Unicode word-splitting doesn't combine hypenated words, but we do::

    >>> [x[0] for x in types_from_string('''
    ...     It had been a close and sultry day--one of the hottest of the
    ...     dog-days--even out in the open country
    ... ''')]
    ['it', 'had', 'been', 'a', 'close', 'and', 'sultry', 'day',
     'one', 'of', 'the', 'hottest', 'of', 'the', 'dog-days',
     'even', 'out', 'in', 'the', 'open', 'country']

    >>> [x[0] for x in types_from_string('''
    ...     so many out-of-the-way things had happened lately
    ... ''')]
    ['so', 'many', 'out-of-the-way', 'things',
     'had', 'happened', 'lately']

We also consider apostrophes surrounding words to be part of the word, unlike
the standard. Preceding apostrophes have to be part of our whitelist though::

    >>> [x[0] for x in types_from_string('''
    ...     'tis 3 days' work. 'twmade-up-word
    ... ''')]
    ["'tis", '3', "days'", 'work', 'twmade-up-word']

Preceding apostrophes have to curve the right direction to be included
as part of the token (and thus the type), so that the first
``’em`` keeps the apostrophe and the second one doesn't::

    >>> [x[0] for x in types_from_string('''
    ...     Closing ’em. Opening ‘em.
    ... ''')]
    ['closing', "'em", 'opening', 'em']

We strip underscores whilst generating types, which are considered part of a
word in the unicode standard::

    >>> [x[0] for x in types_from_string('''
    ... had some reputation as a _connoisseur_.
    ... ''')]
    ['had', 'some', 'reputation', 'as', 'a', 'connoisseur']
"""
import re

import icu
import unidecode

from .icuconfig import DEFAULT_LOCALE

HYPHEN_WORD_PARTS = set((
    # Hyphens from note in http://www.unicode.org/reports/tr29/
    '\u002D',  # HYPHEN-MINUS
    '\u2010',  # HYPHEN
))

APOSTROPHE_WORD_PARTS = set((
    "’",
    "'",
))

#: A list of words that, if prepended with an apostrophe, we should consider
#: the apostrophe part of the token, rather than the start of a quote.
INITIAL_ABBREVIATIONS = set((
    'em',  # e.g. alice.txt: "No, tie ’em together first"
    'tis',
    'twas',
    'twill',
    'twould',
))
INITIAL_ABBREVIATIONS_MAXLEN = max(len(x) for x in INITIAL_ABBREVIATIONS)
INITIAL_ABBREVIATIONS_REGEX = re.compile(r"^(?:%s)\W" % '|'.join(INITIAL_ABBREVIATIONS), re.I)

REGEX_WORD_REMOVALS = re.compile(r'^_|_$')


def word_boundary_type(s, bi, last_b, additional_word_parts=set()):
    """
    Add our own boundary types atop of what bi.getRuleStatus() returns
    """
    if bi.getRuleStatus() > 0:
        # We already think it's a word-boundary, just return
        return bi.getRuleStatus()

    b = bi.current()
    word = s[last_b:b]

    if word in additional_word_parts:
        # Part of additional word parts
        return 200

    if word in HYPHEN_WORD_PARTS:
        # Hyphens are word-parts, but only when surrounded by letters
        # In: over-the-top, 22-skidoo
        # Out: over-, handled--
        def is_wordy(ch):
            return ch in additional_word_parts or ch.isalpha() or ch.isnumeric()
        if not is_wordy(s[b - 2:b - 1]) or not is_wordy(s[b:b + 1]):
            return 0
        return 200

    if word in APOSTROPHE_WORD_PARTS:
        # ICU will handle apostrophe's in words, but not ones before/after.
        # Open-quotes should not be trailing possessives, e.g. cows' milk
        if s[b - 2:b - 1] == 's':
            return 200
        # For select words, hyphen should be part of the word
        if re.search(INITIAL_ABBREVIATIONS_REGEX, s[b:b + INITIAL_ABBREVIATIONS_MAXLEN + 1]):
            return 200

    return 0


def types_from_string(s, offset=0, additional_word_parts=set()):
    """
    Extract tuples of (type, start, end) from s, optionally adding (offset) to
    the start and end values
    """
    def get_token(word_start, word_end):
        """Return (type, start, end)"""
        ttype = s[word_start:word_end].lower()
        ttype = unidecode.unidecode(ttype)
        ttype = re.sub(REGEX_WORD_REMOVALS, '', ttype)
        return (
            ttype,
            word_start + offset,
            word_end + offset,
        )

    bi = icu.BreakIterator.createWordInstance(DEFAULT_LOCALE)
    bi.setText(s)

    out = [None]
    last_b = 0
    word_start = None
    for b in bi:
        if word_boundary_type(s, bi, last_b, additional_word_parts) > 0:
            if word_start is None:
                # This boundary has something word-y before it, start a word
                word_start = last_b
        elif word_start is not None:
            # A non-wordy boundary but a word still open, finalise it
            yield get_token(word_start, last_b)
            word_start = None
        last_b = b
    if word_start is not None:
        # At end, finish any final word
        yield get_token(word_start, last_b)

    # Convert token list to types
    # NB: This needs to be developed in lock-step with client/lib/concordance_utils.js
    return (unidecode.unidecode(s.lower()) for s in out)
