CLiC: A corpus tool to support the analysis of literary texts
=============================================================

The CLiC Dickens project demonstrates through corpus stylistics how computer-assisted methods can be used to study literary texts and lead to new insights into how readers perceive fictional characters. As part of the project we are developing the web app CLiC, designed specifically for the analysis of literary texts. CLiC Dickens started at the University of Nottingham in 2013, it is now a collaborative project with the University of Birmingham. 

CLiC code is divided into 2 halves, the python API server in ``server/`` and the HTML/Javascript client in ``client/``.

Documentation for CLiC is stored in ``doc/``.

For more information, cf. `CLiC Dickens - University of Birmingham <http://www.birmingham.ac.uk/schools/edacs/departments/englishlanguage/research/projects/clic.aspx/>`_.

Prerequisites
-------------

First, configure your system to include the Yarn repository: https://yarnpkg.com/lang/en/docs/install/

...then the nodejs repository::

    curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
    echo "deb https://deb.nodesource.com/node_6.x xenial main" > /etc/apt/sources.list.d/nodesource.list
    apt-get update

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
    chmod -R o+rw server/cheshire3-server/dbs/dickens/{indexes,stores,c3.sqlite}

Configuration & compilation
---------------------------

There a host of variables that can be customised in  ``.local-conf``. The
options will depend on your environment, the following is a minimal example::

    cat <<EOF > .local-conf
    CLIC_MODE="production"
    SERVER_NAME="clic.bham.ac.uk"
    GA_KEY="UA-XXXXX-Y"
    EOF

Generally, the only one to override is SERVER_NAME, which controls what DNS
names the server will respond to. Multiple server names can be used,
separated by spaces. For futher options, read the source of ``install.sh``.

Download dependencies and compile both server/client by running::

    make

Next, run ``install.sh`` as root. This script automates the following steps:

* Configure systemd to launch the UWSGI process running CLiC, and start it
  if in production mode.
* Create / update an NGINX site config to use CLiC, and get NGINX to reload
  the config.

Run with the following::

    sudo ./install.sh

Once this is done CLiC should be available for use.

If you need to stop/start CLiC outside this for whatever reason, use systemctl,
e.g. ``systemctl stop clic``.

Troubleshooting
---------------

If you cannot connect to CLiC from a web browser:

* Make sure you used a SERVER_NAME that matches the server
* Make sure NGINX started without errors: ``systemctl status -ln50 nginx``

If you see the "CLiC is down for maintenance" page:

* Make sure CLiC has started without errors: ``systemctl status -ln50 clic``

If you see errors about missing tables, or queries are particularly slow:

* The RDB may be out of date. run ``./server/bin/recreate_rdb``.

Back-up / generating dumps from live instances
----------------------------------------------

You can generate dumps from a running instance for backup / transfer::

    tar -C server/cheshire3-server/dbs/dickens -jcvf cheshire3.db_dickens.tar.bz2 \
        indexes stores c3.sqlite

Acknowledgements
----------------

This work was supported by the Arts and Humanities Research Council grant reference AH/K005146/1
 
Please reference CLiC as the following:
 
Michaela Mahlberg, Peter Stockwell, Johan de Joode, Catherine Smith, Matthew Brook O’Donnell (forthcoming). “CLiC Dickens – Novel uses of concordances for the integration of corpus stylistics and cognitive poetics”, *Corpora*

This work is released under `AGPL-v3 <LICENSE.rst>`__.
