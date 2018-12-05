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

Click onto the dropdown **'Show subsets'** (see
Figure) to select a relevant
subset (short suspensions, long suspensions, quotes or non-quotes). You
will also need to choose a corpus.

.. figure:: images/figure-analysis-subsets-show-options.png
   :alt: figure-analysis-subsets-show-options

   The basic subset options

Figure shows sample
lines from the subset of long suspensions in *Oliver Twist*. You can
then use the filter option to narrow down the lines and group them using
the KWICGrouper. As in the concordance tab, you can create tags to
annotate rows with noteworthy patterns

.. figure:: images/figure-analysis-subsets-show-longsuspensions.png
   :alt: figure-analysis-subsets-show-longsuspensions

   The first few lines from the subset of 'long suspensions'
   in Oliver Twist

.. rubric:: Results
   :name: results-1

Like in the concordance tab, this allows you to adjust the way the
concordance output ('table') is displayed.

.. rubric:: Filter rows
   :name: filter-rows-1

The filter option lets you filter the output by the rows that contain a
particular sequence of letters, as described in Section 5.2 on the
filter function in the Concordance tab. For example, you could filter
suspensions for particular speech verbs like *cried*
(Figure).

.. figure:: images/figure-analysis-subsets-results-filter-cried.png
   :alt: figure-analysis-subsets-results-filter-cried

   Filtering long suspensions in Oliver Twist for cried

.. figure:: images/figure-analysis-subsets-results-filter-cotext.png
   :alt: figure-analysis-subsets-results-filter-cotext

   Filtering the co-text of long suspensions for perhaps in
   Oliver Twist

Note, however, that the filter will search through the whole row and
therefore also accounts for words in the context, not only in the subset
itself. For example, when searching through the subset of long
suspensions in *Oliver Twist* and filtering rows for *perhaps* the
results originate only from the co-text, as *perhaps* does not occur in
long suspensions (see
Figure).

.. rubric:: KWICGrouper
   :name: kwicgrouper-1

If you want to restrict your search to the subset itself, the
KWICGrouper is the better option; it will also highlight your search
terms, as described in Section 5.2 on concordances. The Subset
KWICGrouper works like the Concordance KWICGrouper, with the exception
of its search span which operates only on the subset itself. See
Figure
for an illustration of the Subset KWICGrouper searching for lines with
*cried*, *screamed* and *sobbed*.

.. figure:: images/figure-analysis-subsets-kwicgrouper-criedscreamedsobbed.png
   :alt: figure-analysis-subsets-kwicgrouper-criedscreamedsobbed

   The search span of the Subset KWICGrouper applies to the
   subset; not to the co-text

.. rubric:: Manage tag columns
   :name: manage-tag-columns-1

.. figure:: images/figure-analysis-subsets-tagcolumns-gender.png
   :alt: figure-analysis-subsets-tagcolumns-gender

   Tagging subsets – here, long suspensions in ChiLit
   containing cried are tagged for character gender

Just like in the Concordance tab (Section 5.2), subset rows can be
annotated with user-defined tags.
Figure shows a
potential application of tagging subsets: long suspensions in the 19th
Century Children's Literature (ChiLit) corpus containing *cried* are
tagged for whether the crying character is male or female. Note that
this screenshot just illustrates the technique; it does not represent
the actual gender distribution of *cried* in the ChiLit long
suspensions.