Developing the system
=====================

Set-up of the development environment is very similar to a production
environment, see README.rst for details on how to do this.

The main difference is to use ``PROJECT_MODE="development"`` (or not include any
PROJECT_MODE, development is default), in your ``local-conf.mk``. This will stop
CLiC from being started automatically so you can run the server in debug mode.
It will also disable NGINX's server cache so you won't get stale responses.

To start the API server in debug mode::

    make start

Client-side development
-----------------------

To run tests, lint code and compile::

    make -C client

...you will need to do this after any change to the HTML/CSS/JS source.

Server-side development
-----------------------

To run unit tests::

    make -C server test

Exercise API integration tests
------------------------------

This repository contains some canned API calls and output that can be run against
any server. For example::

    ./exercise.sh http://cal-n-clic-01.bham.ac.uk exercise_outputs/*

Favico regeneration
-------------------

Upload ``assets/logo.svg`` to http://cthedot.de/icongen/, and place the results into
```client/www/index.html`` and ``client/www/iconx`` as appropriate.
