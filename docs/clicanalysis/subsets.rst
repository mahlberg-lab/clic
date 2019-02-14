Subsets
=======

The Subsets tab can display the full subset of your choice for the
selected corpus. Therefore, you can retrieve all quotes or all long
suspensions, etc. in any of the books or pre-selected corpora for
further analysis. Note that we find this option most useful for the
smaller subsets, i.e. quotes and suspensions; if you select the whole
'non-quotes' subset the output may become unwieldy.

.. rubric:: Show subsets
   :name: show-subsets

Click onto the dropdown **'Show subsets'** (see :numref:`figure-analysis-subsets-show-options`) to select a relevant
subset (short suspensions, long suspensions, quotes or non-quotes). You
will also need to choose a corpus.

.. _figure-analysis-subsets-show-options:
.. figure:: ../images/figure-analysis-subsets-show-options.png

   The basic subset options

:numref:`figure-analysis-subsets-show-longsuspensions` shows sample
lines from the subset of long suspensions in *Oliver Twist*. You can
then use the filter option to narrow down the lines and group them using
the KWICGrouper. For subsets, the "relative frequency" is not given in terms of
frequency per million words, as in the Concordance tab, but as the percentage of
total words in the corpus found in the selected subset.

.. _figure-analysis-subsets-show-longsuspensions:
.. figure:: ../images/figure-analysis-subsets-show-longsuspensions.png

   The first few lines from the subset of 'long suspensions'
   in Oliver Twist

.. rubric:: Results
   :name: results-1

Like in the concordance tab, this allows you to adjust the way the
concordance output ('table') is displayed.

.. rubric:: Filter rows
   :name: filter-rows-1

The filter option lets you filter the output by the rows that contain a
particular sequence of letters, as described in the :ref:`Filter rows`
subsection of the Concordance tab documentation. For example, you could filter
suspensions for particular speech verbs like *cried*
(:numref:`figure-analysis-subsets-results-filter-cried`).

.. _figure-analysis-subsets-results-filter-cried:
.. figure:: ../images/figure-analysis-subsets-results-filter-cried.png

   Filtering long suspensions in Oliver Twist for *cried*

.. _figure-analysis-subsets-results-filter-cotext:
.. figure:: ../images/figure-analysis-subsets-results-filter-cotext.png

   Filtering the co-text of long suspensions for *perhaps* in
   Oliver Twist

Note, however, that the filter will search through the whole row and
therefore also accounts for words in the context, not only in the subset
itself. For example, when searching through the subset of long
suspensions in *Oliver Twist* and filtering rows for *perhaps* the
results originate only from the co-text, as *perhaps* does not occur in
long suspensions (see :numref:`figure-analysis-subsets-results-filter-cotext`).

.. rubric:: KWICGrouper
   :name: kwicgrouper-1

If you want to restrict your search to the subset itself, the
KWICGrouper is the better option; it will also highlight your search
terms, as described in the :ref:`Concordance` section. The Subset
KWICGrouper works like the Concordance KWICGrouper, with the exception
of its search span which operates only on the subset itself. See
:numref:`figure-analysis-subsets-kwicgrouper-criedscreamedsobbed`
for an illustration of the Subset KWICGrouper searching for lines with
*cried*, *screamed* and *sobbed*.

.. _figure-analysis-subsets-kwicgrouper-criedscreamedsobbed:
.. figure:: ../images/figure-analysis-subsets-kwicgrouper-criedscreamedsobbed.png

   The search span of the Subset KWICGrouper applies to the
   subset; not to the co-text

.. rubric:: Manage tag columns
   :name: manage-tag-columns-1

.. _figure-analysis-subsets-tagcolumns-gender:
.. figure:: ../images/figure-analysis-subsets-tagcolumns-gender.png

   Tagging subsets – here, long suspensions in ChiLit
   containing *cried* are tagged for character gender

Just like in the Concordance tab (see :ref:`Concordance`), subset rows can be
annotated with user-defined tags.
:numref:`figure-analysis-subsets-tagcolumns-gender` shows a
potential application of tagging subsets: long suspensions in the 19th
Century Children's Literature (ChiLit) corpus containing *cried* are
tagged for whether the crying character is male or female. Note that
this screenshot just illustrates the technique; it does not represent
the actual gender distribution of *cried* in the ChiLit long
suspensions.