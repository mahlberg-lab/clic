Glossary of terms used
======================

book:
    A UTF-8 encoded text file that has been imported into CLiC, invariably from the corpora repository.

region:
    A labelled portion of a book. Each region will have:

    * A name (or rclass), for example 'chapter.sentence'. For all possible names, see `10-rclass.sql <../schema/10-rclass.sql>`__.
    * A start and end character position within the full book text
    * (optionally) a number (or rvalue), for example it's position within a chapter.

    Regions are added by *region tagger* scripts, which are in :mod:`clic.region`.

token:
    A token is a labelled portion of a book that contains a single word.
    In the phrase ``'For _more_!' said Mr. Limbkins.``, ``For``, ``more``, ``said``, ``Mr``, ``Limbkins`` would be tokens.

    See :mod:`clic.tokenizer`.

type/ttype:
    A token has a type (thus ttype). This is a normalised form of the token.
    The tokens in the phrase ``'For _more_!' said Mr. Limbkins.`` would have types ``for``, ``more``, ``said``, ``mr``, ``limbkins``.

    See :mod:`clic.tokenizer`.
