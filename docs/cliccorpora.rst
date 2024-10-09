The CLiC corpora
================

An overview of the corpora available in CLiC can be seen from the Counts tab. 
Simply choose the corpus for which you want to see the list of books and the 
Counts tab will provide a table listing the names and word counts for each book, 
per subset and in total.

For a full list of titles in CLiC please refer to Appendix 1.
The procedure followed for retrieving, cleaning and importing the most
recent texts is described in detail in our [GitHub_corpora]_
repository. Every change ("commit") to the repository is marked with a "commit" number (actually a sequence of characters and numbers) in GitHub, circled in green in :numref:`figure-version-numbers-github`. From CLiC 2.0.0 onwards, this "commit" number is also displayed on the CLiC interface – circled in green in :numref:`figure-version-numbers`– to indicate which version of the corpora is used. **We recommend that users record both the version number of CLiC itself** (displayed directly under the CLiC logo, circled in red in :numref:`figure-version-numbers`, i.e. in this case "2.0.0") **and the version of the corpora** (i.e. in this case "db61de3") **when saving results**. This ensure that if at a later stage there should be differences in search results it is possible to investigate which changes to the interface or the corpora caused this discrepancy.

.. _figure-version-numbers-github:
.. figure:: images/figure-version-numbers-github.png

   The "commit" version number of the Github corpora repository

.. _figure-version-numbers:
.. figure:: images/figure-version-numbers.png

   The CLiC release and corpora version numbers in the CLiC interface


The Corpora repository also contains the full text of the corpus files 
after any manual cleaning changes have been implemented. The history of the 
Corpora repository lists the changes and you can refer to the original versions, 
as downloaded from the Project Gutenberg page for:

* the ArTs corpus [GitHub_corpora_initial_ArTs]_ (note that the
  ArTs corpus used to be called "Other", hence that name in the repository's history)
* the ChiLit corpus [GitHub_corpora_initial_ChiLit]_

The texts can be
selected individually and combined freely for analysis in any of the
CLiC tools. You can also choose from
one of our four pre-selected corpora: DNov – Dickens's Novels (15
texts), 19C – 19th Century Reference Corpus (29 texts), ChiLit – 19th
Century Children's Literature Corpus (71 texts) and ArTs – Additional
Requested Texts (31 texts). ArTs includes additional GCSE and A-Level
titles (please see Appendix 2 for an overview of all CLiC texts listed
in the AQA, OCR and Edexcel GCSE and A-Level English specifications).
The ArTs corpus was not designed to be analysed as a whole, but rather to
add individual requests to CLiC.

In order to **select texts** in any of the CLiC analysis tabs, go to
controlbar on the right-hand side. You can select any or all of
the texts by picking the corpora from a drop-down list or typing their
names into a textbox. For example, in the Concordance tool, once you
have clicked on the Concordance tab, a textbox labeled **'Search the
corpora'** will appear (see the :ref:`Concordance` section), 
as illustrated in :numref:`figure-corpora-select` and :numref:`figure-corpora-select_2`.

.. _figure-corpora-select:
.. figure:: images/figure-corpora-select.png

   Selecting corpora in the Concordance tab (same procedure
   in Subsets and Clusters; see the :ref:`Keywords` section on how to
   select target and reference corpora)
   
.. _figure-corpora-select_2:   
.. figure:: images/figure-corpora-select_2.png

   The dropdown menu for selecting corpora

You can search the pre-selected corpora in their entirety or you can
pick individual books from them, effectively creating your own
subcorpus. For example, you could select several books from Dickens,
several books from the 19th Century Reference Corpus (19C) and several
books from the 19th Century Children's Literature Corpus (ChiLit). 

You can also select an author-based corpus from the drop-down. For example,
typing *austen* into the textbox (which is not case-sensitive) gives you the option of selecting all 
books by Jane Austen at once, as illustrated in :numref:`figure-corpora-authorbased`.

.. _figure-corpora-authorbased:
.. figure:: images/figure-corpora-authorbased.png

   Example of creating an author-based corpus:
   selecting all of Jane Austen's novels

The CLiC corpora have been marked up to distinguish between several
textual subsets of novels. The example
from *Great Expectations* below illustrates the subsets and :numref:`figure-corpora-markupsubsets` shows how these are marked up
in the chapter views, which can be retrieved from the 'in bk.' (in book)
button in concordances (see the :ref:`Concordance` section for details)
and the Text tab. The "in book" view also contains a legend of the markup
layers (see :numref:`figure-corpora-highlight-subsets`), which you can
individually select and deselect.

::

    "And on what evidence, Pip," asked Mr. Jaggers, very coolly, as he
    paused with his handkerchief half way to his nose,"does Provis make
    this claim?”

    "He does not make it," said I, "and has never made it, and has no
    knowledge or belief that his daughter is in existence.”

    For once, the powerful pocket-handkerchief failed. My reply was so
    unexpected that Mr. Jaggers put the handkerchief back into his pocket
    without completing the usual performance, folded his arms, and looked
    with stern attention at me, though with an immovable face.

[*Great Expectations*, Chapter 51]

-  quotes: any text listed in quotes, i.e. mostly character speech but
   also thoughts or songs that might appear in quotes
-  non-quotes: narration

   -  and a special case of non-quotes, suspensions, which represent
      narratorial interruptions of character speech that do not end with
      sentence-final punctuation. Suspensions are further divided by
      length:

      -  short suspensions have a length up to four words
      -  long suspensions have a length of five or more words

.. _figure-corpora-markupsubsets:
.. figure:: images/figure-corpora-markupsubsets.png

   Chapter view of example (1) (retrieved via the 'in bk.'
   (in book) button in a concordance of asked Mr Jaggers very coolly),
   exemplifying the mark-up of subsets
   
.. _figure-corpora-highlight-subsets:
.. figure:: images/figure-corpora-highlight-subsets.png

    Example of highlighting subsets

The rationale behind the division of the subsets can be found in the open access article by
[Mahlberg_et_al_2016]_. The procedure described in that article refers to the
earliest CLiC corpora, DNov and 19C. The tagging procedure for the most recently added
corpora – ChiLit and ArTs – differs in the technical implementation – see :mod:`clic.region` for details.
