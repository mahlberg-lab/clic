* client/index: Add links to paper, maintenance schedule, documentation

## 2.0.0 (2019-01-31)

* client/controlbar: Allow searching for parts of words in chosen dropdowns
* tagger/chapter: Add EPILOGUE to list of magic chapter words
* client/filesystem: Ensure newlines are escaped when saving CSV output

## 2.0.0-beta7 (2019-01-15)

* client: Update institution logos
* server/migrate/cheshire_json: Don't mangle chapter headings
* client/text: Remember position in book last scrolled to
* server/region/suspension: Redefine suspensions, ignoring sentence breaks in quotes before
* server: Bump PyYAML for CVE-2017-18342
* client/concordance: Show pilcrow marks at paragraph breaks
* cluster: Tie-break sorting of clusters alphanumerically
* server/concordance: More intelligent choice of anchor nodes, speeding up queries
* install: Add HTTPS support

## 2.0.0-beta6 (2018-12-12)

* server/cluster: Improve cluster performance
* tagger/quote: Don't mis-tag starts of chapters as suspensions

## 2.0.0-beta5 (2018-12-07)

* client/table: Don't stay on current page if query changes
* client/text: Make sure there's padding around text in mobile views

## 2.0.0-beta4 (2018-11-30)

* server/region_preview: Add (temporary!) endpoint for previewing regions
* server: API should respond to POST requests as well as GET
* server/region_preview: Read from stdin by default
* docs: Make /docs deep-redirect to readthedocs, add link in help
* install: Remove generated deploy.sh scripts, just use "make install" instead

## 2.0.0-beta3 (2018-11-27)

* text: Preserve white-space before indented text (e.g. songs)

## 2.0.0-beta2 (2018-11-22)

* server: Make sure initial errors are thrown as a 500 status
* concordance: Fix count of unique books, add "pm" unit
* client: Add new CLiC logo
* subset: Ignore empty regions, e.g. empty suspensions in ArTs

## 2.0.0-beta1 (2018-11-21)

* server: Complete rewrite:
  * Remove cheshire3/sqlite with
  * Add a unified postgresql database for all content
  * Upgrade to Python3
* tokenisation: Defined tokenisation scheme based on unicode standard rules, used both for queries and importing books, see server/clic/tokenizer.py
* tokenisation: Any surrounding punctuation is filtered from types, thus searching for "connisseur" will return tokens "connisseur" and "_connisseur_" [BREAKING CHANGE]
* concordance: Wildcards can now be used in queries, e.g. "he * her hair", "Oliver*"
* concordance: Search is now for exact types. "Oliver" will no longer return "Oliver's" results, you must explicitly enter "Oliver*" [BREAKING CHANGE]
* region: Re-defined region tagging based on unicode standard rules, used when importing books, see server/clic/region
* region: Initial text between parts and chapters is now part of the previous chapter, instead of being in it's own chapter. This will reduce chapter counts for books broken up into parts. [BREAKING CHANGE]
* text: Shows book content verbatim from corpora repo, allows copy and paste
* text: Hide embedded suspensions, since we no longer mark them up
* cluster: Clusters now ignores boundaries, and only pays attention to token order. i.e. clusters can span adajcent quotes, but not chapters (as the title is in the way) [BREAKING CHANGE]
* migrate: Pull corpora information directly from corpora.bib
* keyword: Click on keyword clusters to see concordance lines
* concordance: Support single-character ? as well as *, e.g. "To the ?th degree"

## 1.7-beta3 (2018-09-21)

* subset: Use percentage of text instead of relative frequency
* homepage: Add carousel of images
* client: Option for searching for "All books by author"
* keywords: Add swap button to reverse ref/target options
* text: Show entire book on text tab

## 1.7-beta2 (2018-08-14)

* text: Add text tab or showing book contents
* count: Add Counts tab for showing counts of words within books

## 1.7-beta1 (2018-05-28)

* api: Rearrange per-result metadata, still not to be relied on yet
* concordance/subset: Add chapter ticks to distribution plot
* concordance/subset: Make full book titles available in concordance/subset view
* concordance/subset: Add API option for returning book titles
* concordance/subset: Add distribution plot view
* concordance: Book name column should always be visible
* concordance: Don't highlight terms when concordance metadata is hidden
* clusters: If only one book is selected, frequency cutoff is 2
* Only preserve pages after reload if the page exists
* Remove Expected target/ref columns from Keywords view
* Link cluster lines to a matching concordance search
* Update page title on page changes
* Make error/warning/info reporting more consistent
* Add basic twitter, opengraph preview support

## 1.6.2 (2018-03-11)

* Fix nonquote/all subset queries when a chapter is empty
* Code samples for direct CLiC API usage
* Remove useless "0 from start" option in KWICGrouper

## 1.6.1 (2017-11-08)

* Work around file-handle leaks in cheshire3
* Row selection fixes
* Fix /subsets redirect
* Add CLiC & corpora versions to every API response
* Empty CLiC cache on re-install
* Fix header colour

## 1.6.0 (2017-11-02)

* Rework entire CLiC codebase & repository, removing old code and large commits. Old code is available at https://github.com/birmingham-ccr/clic-legacy
* Split CLiC into distinct REST API and clientside SPA parts
* Rework CLiC UI 
