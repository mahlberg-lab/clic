Developing the system
=====================

Set-up of the development environment is very similar to a production
environment, see README.rst for details on how to do this.

The main difference is to use ``CLIC_MODE="development"`` (or not include any
CLIC_MODE, development is default), in your ``.local-conf``. This will stop
CLiC from being started automatically so you can run the server in debug mode
with ``make start``. It will also disable NGINX's server cache so you won't get
stale responses

Client-side development
-----------------------

To run tests, lint code and compile::

    make -C client

...you will need to do this after any change to the HTML/CSS/JS source.

Server-side development
-----------------------

Start the API server server in debug mode::

    make start

To run unit tests::

    make -C server test

Exercise API integration tests
------------------------------

This repository contains some canned API calls and output that can be run against
any server. For example::

    ./exercise.sh http://cal-n-clic-01.bham.ac.uk exercise_outputs/*

Useful utilities
----------------

The following utilities can be useful::

    sudo apt-get install db-util sqlite3

You can get at the cheshire3 objects on the command line with::

    ./bin/python
    >>> from clic import ClicDb
    >>> cdb = ClicDb()
    >>> cdb.c3_query(...)

Favico regeneration
-------------------

Upload ``assets/logo.svg`` to http://cthedot.de/icongen/, and place the results into
```client/www/index.html`` and ``client/www/iconx`` as appropriate.
