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
