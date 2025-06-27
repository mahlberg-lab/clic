FlexiConc
=========

Clicking onto the **'FlexiConc'** tab will take you to the FlexiConc
view. In order to create a flexiconc analsis tree, you will need to select a corpus
to search in (see :ref:`The CLiC corpora`).

Search the corpora
------------------

This is where you select a corpus to search in. The
selection is very flexible and lets you pick a pre-defined corpus (see :ref:`The CLiC corpora`)
or choose your own subcorpus – with any of the books available in CLiC.

Only in subsets
---------------

Here you can decide whether you want to search through 'all text' – the
whole book(s) – or just one of the subsets: 'short suspensions', 'long
suspensions', 'quotes' and 'non-quotes' (see :ref:`The CLiC corpora`).

Search for terms
----------------

This is the fundamental parameter of the concordance search – it lets
you determine the node word or phrase that forms the basis of the
concordance.


The tokenisation from CLiC 2.0 onwards is based on unicode standard rules
(i.e. Unicode word boundaries implemented with the [ICU]_ library), used
both for queries and importing books.

We consider a boundary mark to be a word-boundary if...
* The [ICU]_ library describes it as at the end of a word, e.g. ``jump`` or number, e.g. ``32.3``.
* It is a single hyphen character surrounded by alpha-numeric characters.
* It is an apostrophe preceded with ``s``, e.g. ``3 days' work``.
* It is one of a whitelist of words preceded with an apostrophe, e.g. ``'tis``.

CLiC 2.0 and onwards supports **wildcards**:

* ``*`` means "zero or more characters", for example:
  
  Placing * at the end of a the sequence ``can`` serves as a placeholder for
  any sequence of characters (or zero) and therefore retrieves all instances of 
  words starting with this sequence, including ``can``, ``cannot`` and ``can't``
  (but also ``candle``, ``candles``, ``candlestick`` etc.)
  
  ``*`` in ``with * hands`` serves as a placeholder for any word token
  between ``with`` and ``hands``, retrieving sequences like ``with her hands``, 
  ``with his hands``, ``with their hands``, ``with both hands``, 
  ``with clean hands`` etc.

* ``?`` means "one"

The search will only retrieve valid tokens according to the rules above.
This means that the search will ignore punctuation in your search query except for 
punctuation sign will not retrieve any results. If your research focuses
on punctuation markers you can evade this issue by using the filter
function in the subset tab: Go to the subset tab, select the relevant
subset, for example non-quotes, and filter the rows to the punctuation
marker of interest.
Two hyphens separate words: for example, *Char--lotte* in Oliver
Twist (OT.c6.p20) “Oliver's gone mad! Char--lotte!” counts as two
tokens.

For the detailed technical documentation and more examples see :mod:`clic.tokenizer`.

'Whole phrase' or 'Any word'
----------------------------

When you have entered several terms, you need to specify whether it is
to be searched as one phrase (equivalent to using double quotes in a
search engine, e.g. *dense fog*) or any of the words individually
(*dense* and *fog*).
