Documentation
-------------

readthedocs is used for our documentation. In order for newly released versions of CLiC (as managed by tags, e.g. v2.1.2) to be included in readthedocs please make sure to follow the above instructions in 'Preparing a release' when updating CLiC on the production server.

You can access the settings for CLiC's readthedocs by going to: https://readthedocs.org/projects/clic/

On this page, there should be a line for each CLiC branch / major.minor version, and 'latest'. When a new branch is started in CLiC the corresponding branch needs to be added to readthedocs, otherwise there will be a 404 error when selecting the "help" link. If a new branch is missing, go to the above page and...

# "Add version"
# Search for the branch number in the box
# Turn on "Active"
# Click "Update version"

You should also change the default branch by...

# "Settings" in top-right corner
# Select new default branch in drop-down

If you need maintainer access, please request from an existing maintainer.

Sphinx will also be run locally for testing, and if it proves useful in future.

To re-build documentation::

    make -C docs

To view the documenation built, go to ``/local-docs/`` for your instance.

By default, this only generates the LaTeX needed for the PDF output, which will
be available in ``docs/_build/latex/clic-userguide.tex``. To build a PDF from
this, you first need to install::

    apt install texlive-latex-recommended \
                texlive-fonts-recommended \
                texlive-latex-extra \
                latexmk

...then you can build with::

    make -C docs pdf

The pdf will be available at ``/local-docs/latex/clic-userguide.pdf``.
