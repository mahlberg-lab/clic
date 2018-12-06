Developing the system
=====================

Set-up of the development environment is very similar to a production
environment, see README.rst for details on how to do this.

The main difference is to use ``PROJECT_MODE= development`` (or not include any
PROJECT_MODE, development is default), in your ``local-conf.mk``. This will stop
CLiC from being started automatically so you can run the server in debug mode.
It will also disable NGINX's server cache so you won't get stale responses.

To start the API server in debug mode::

    make start

To log database queries that the API makes::

     QUERY_LOG=yes make start
     QUERY_LOG=explain make start  # Also include explain plan

Client-side development
-----------------------

To run tests, lint code and compile::

    make -C client

...you will need to do this after any change to the HTML/CSS/JS source.

Server-side development
-----------------------

To run unit tests::

    make -C server test

Coverage reports
----------------

Coverage reports can be built for both client and server::

    make coverage

...the reports will be available through the reports at the end.

Exercise API integration tests
------------------------------

This repository contains some canned API calls and output that can be run against
any server. For example::

    ./exercise.sh http://cal-n-clic-01.bham.ac.uk exercise_outputs/*

Favico regeneration
-------------------

Upload ``assets/logo.svg`` to http://cthedot.de/icongen/, and place the results into
```client/www/index.html`` and ``client/www/iconx`` as appropriate.

Documentation
-------------

Whilst generally we use readthedocs for documentation sphinx will also be run
locally for testing, and if it proves useful in future.

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
