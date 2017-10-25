CLiC API usage
==============

The CLiC API can also be queried directly and JSON returned.

For tracking purposes, please set the User Agent and "X-Clic-Client" header to
something that identifies your application.

For more information on particular endpoints, please see the documentation in:

* ``server/clic/metadata.py``: For corpora metadata (e.g. book names)
* ``server/clic/subset.py``: For text subsets (e.g. quotes / suspensions) or entire chapters
* ``server/clic/concordance.py``: For concordance searches
