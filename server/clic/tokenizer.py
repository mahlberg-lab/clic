"""
This module provides the core tokenisation used in CLiC, used both when parsing
incoming texts and when parsing concordance queries

Method
------

To extract tokens, we use Unicode text segmentation as described in [UAX29],
using the implementation in the [ICU] library and standard rules for en_GB.

Please read the document for a full description of ICU word boundaries, however
as a quick example the following phrase::

    The quick (“brown”) fox can’t jump 32.3 feet, right?

...would have boundaries at every point marked with a ``|``::

    The| |quick| |(||“|brown|”|)| |fox| |can’t| |jump| |32.3| |feet|,| |right|?|

If the ``|`` marks the end of a word/numeric section, we consider everything
until the last ``|`` mark a token.

Tokens are normalised into types by:-

* Lower-casing, ``The`` -> ``the``.
* Normalising any non-ascii characters with [UNIDECODE], e.g.
  * ``can’t`` -> ``can't``.
  * ``café`` -> ``cafe``.
* Removing any surrounding underscores, e.g. ``_connoisseur_`` -> ``connoisseur``.

In addition, when parsing a query we treat ``*`` as being part of a word, so
``*Books*`` would result in ``*books*`` in query mode, and ``books`` otherwise.

Examples / edge cases
---------------------

A type is lower-case, ASCII-representable term, and "fancy" apostrophe's are normalised::

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

Unicode word-splitting doesn't combine hypenated words::

    >>> [x[0] for x in types_from_string('''
    ...     It had been a close and sultry day--one of the hottest of the
    ...     dog-days--even out in the open country
    ... ''')]
    ['it', 'had', 'been', 'a', 'close', 'and', 'sultry', 'day',
     'one', 'of', 'the', 'hottest', 'of', 'the', 'dog', 'days',
     'even', 'out', 'in', 'the', 'open', 'country']

    >>> [x[0] for x in types_from_string('''
    ...     so many out-of-the-way things had happened lately
    ... ''')]
    ['so', 'many', 'out', 'of', 'the', 'way', 'things',
     'had', 'happened', 'lately']

We strip underscores whilst generating types, which are considered part of a
word in the unicode standard::

    >>> [x[0] for x in types_from_string('''
    ... had some reputation as a _connoisseur_.
    ... ''')]
    ['had', 'some', 'reputation', 'as', 'a', 'connoisseur']

Unlike regular parsing, query parsing preserves asterisks and converts them
into percent marks for use in database concordance queries::

    >>> [x[0] for x in types_from_string('''
    ... Moo* * oi*-nk
    ... ''')]
    ['moo', 'oi', 'nk']

    >>> parse_query('''
    ... Moo* * oi*-nk
    ... ''')
    ['moo%', '%', 'oi%', 'nk']


References
----------

.. [ICU] http://userguide.icu-project.org/boundaryanalysis
.. [UAX29] https://www.unicode.org/reports/tr29/tr29-33.html#Word_Boundaries
.. [UNIDECODE] https://pypi.org/project/Unidecode/
"""
import re

import icu
import unidecode

from .icuconfig import DEFAULT_LOCALE

QUERY_ADDITIONAL_WORD_PARTS = set((
    '*',  # Consider * to be part of a type, so we can use it as a wildcard
))

REGEX_WORD_REMOVALS = re.compile(r'^_|_$')


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
        if bi.getRuleStatus() > 0 or s[last_b:b] in additional_word_parts:
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


def parse_query(q):
    """
    Turn a query string into a list of LIKE expressions
    """
    def term_to_like(t):
        """Escape any literal LIKE terms, convert * to %"""
        return (t.replace('\\', '\\\\')
                 .replace('%', '\\%')
                 .replace('_', '\\_')
                 .replace('*', '%'))

    return list(term_to_like(t) for t, word_start, word_end in types_from_string(q, additional_word_parts=QUERY_ADDITIONAL_WORD_PARTS))
