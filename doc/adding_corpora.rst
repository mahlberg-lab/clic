Uploading new texts
===================

The raw texts for CLiC to process are assumed to be in the corpora repository:

    https://github.com/birmingham-ccr/corpora

If you haven't done so already, add the texts to this repository, following the instructions there.

For each new book, first check the region annotation using, for example::

    ./server/bin/region_preview corpora/ChiLit/alone.txt

This will show the text file with all regions marked up with different colours.
Inspect the output to see if regions are marked up correctly by default. If the scripts have made mistakes, you have 2 options:

* Fix any systematic problems in the region taggers in ``server/clic/region``
* Export the tagged regions to a ``*.regions.csv`` file, which will override the tagger.

Once you are happy with the output, it needs to be imported into the CLiC database.
Do not perform the following on a live CLiC server, as CLiC will not be available during the process.
Instead, follow the instructions on dumping / restoring a database in `production.rst <production.rst>`__.

``import_corpora_repo`` will import all given texts into the database.
Ideally (re-)import the entire corpora repository with::

    ./server/bin/import_corpora_repo corpora/*/*.txt

...however this takes some time. It is also possible to import individual books::

    ./server/bin/import_corpora_repo corpora/ChiLit/alone.txt

Restart CLiC with ``./install.sh`` to ensure that caches are flushed.
