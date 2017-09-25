CLiC: A corpus tool to support the analysis of literary texts
=============================================================

The CLiC Dickens project demonstrates through corpus stylistics how computer-assisted methods can be used to study literary texts and lead to new insights into how readers perceive fictional characters. As part of the project we are developing the web app CLiC, designed specifically for the analysis of literary texts. CLiC Dickens started at the University of Nottingham in 2013, it is now a collaborative project with the University of Birmingham. 

CLiC code is divided into 2 halves, the python API server in ``server/`` and the HTML/Javascript client in ``client/``.

For more information, cf. `CLiC Dickens - University of Birmingham <http://www.birmingham.ac.uk/schools/edacs/departments/englishlanguage/research/projects/clic.aspx/>`_.

Prerequisites
-------------

First, configure your system to include the Yarn repository: https://yarnpkg.com/lang/en/docs/install/

Then install the following from your system repositories::

    # Server prerequisites
    sudo apt-get install build-essential \
        subversion \
        python-virtualenv virtualenv \
        python2.7 libpython2.7-dev python2.7-dev \
        libxml2-dev libxslt1-dev

    # Client prerequisites
    sudo apt-get install make nodejs yarn nginx

Database setup
--------------

You need to pre-populate your CLiC instance. This requires ``cheshire3.db_dickens.tar.bz2``,
which is available internally. Untar the cheshire3 stores/indexes (NB: this will take some time)::

    tar -C server/cheshire3-server/dbs/dickens -jxf cheshire3.db_dickens.tar.bz2
    chmod o+w server/cheshire3-server/dbs/dickens/stores/*
    chmod o+w server/cheshire3-server/dbs/dickens/indexes/*

Production installation
-----------------------

Download dependencies and compile both server/client by running::

    make

The ``install.sh`` script automates the following steps:

* Configure systemd to launch the UWSGI process running CLiC, and start it
* Create / update an NGINX site config to use CLiC, and get NGINX to reload
  the config.

There a host of variables that can be customised, see the top of the script.
Generally, the only one to override is SERVER_NAME, which controls what DNS
names the server will respond to. Multiple server names can be used,
separated by spaces.

Write any customisation to ``.local-conf``. The options will depend on your
environment, the following is a minimal example::

    cat <<EOF > .local-conf
    CLIC_MODE="production"
    SERVER_NAME="clic.bham.ac.uk"
    EOF

For futher options, read the source of ``install.sh``. Finally, run the script::

    sudo ./install.sh

Once this is done CLiC should be available for use. Next you want to ensure
that the cache is pre-warmed, see "Cache pre-warm".

If you need to stop/start CLiC outside this for whatever reason, use systemctl,
e.g. ``systemctl stop clic``.

Troubleshooting
---------------

If you cannot connect to CLiC from a web browser:

* Make sure you used a SERVER_NAME that matches the server
* Make sure NGINX started without errors: ``systemctl status -ln50 nginx``

If you see the "CLiC is down for maintenance" page:

* Make sure CLiC has started without errors: ``systemctl status -ln50 clic``

Cache pre-warm
--------------

For maximum performance, CLiC stores all chapters in memory. By default these are
read in as they are needed for concordance matches. This means that responses will
be very slow until all chapters have been looked at at least once.

To avoid this, you can force CLiC to read in every chapter in turn, so everything
is ready in memory, and dump this to ``clic-chapter-cache.pickle``, which will be
automatically read when CLiC restarts. To (re)generate this file do the following:
* Start CLiC, either in production or development
* Visit ``http://(server_name)/api/concordance-warm/``, make a cup of tea. You can use
  ``curl`` to run this command on the server to avoid network issues.
* Once it is finished, verify ``clic-chapter-cache.pickle`` exists and restart CLiC
  so all processes use the same cache file.

Back-up / generating dumps from live instances
----------------------------------------------

You can generate dumps from a running instance for backup / transfer::

    tar -C dbs/dickens -jcvf cheshire3.db_dickens.tar.bz2 indexes stores

Developing the system
---------------------

To speed up development, pre-warm the cache as-per the "Cache pre-warm" section.

Start the webserver in debug mode::

    make start

To run unit tests::

    make -C server test
    make -C client test

The following utilities can be useful::

    sudo apt-get install db-util sqlite3

You can get at the cheshire3 objects on the command line with::

    ./bin/python
    >>> from clic import ClicDb
    >>> cdb = ClicDb()
    >>> cdb.c3_query(...)

Favico regeneration
^^^^^^^^^^^^^^^^^^^

Upload ``assets/logo.svg`` to http://cthedot.de/icongen/, and place the results into
```client/www/index.html`` and ``client/www/iconx`` as appropriate.

Uploading new texts
-------------------

From the ``annotation`` directory::

    ./annotate.sh ../corpora/ChiLit ./ChiLit_out

From the ``server`` directory::

    ./bin/python
    >>> from clic.clicdb import ClicDb ; cdb = ClicDb()
    >>> cdb.store_documents('/srv/devel/bham.clic/annotation/ChiLit_out/final/')


Acknowledgements
----------------

This work was supported by the Arts and Humanities Research Council grant reference AH/K005146/1
 
Please reference CLiC as the following:
 
Michaela Mahlberg, Peter Stockwell, Johan de Joode, Catherine Smith, Matthew Brook O’Donnell (forthcoming). “CLiC Dickens – Novel uses of concordances for the integration of corpus stylistics and cognitive poetics”, *Corpora*

This work is released under `AGPL-v3 <LICENSE.rst>`__.
