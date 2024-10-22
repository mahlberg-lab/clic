CLiC: A corpus tool to support the analysis of literary texts
=============================================================

The CLiC Dickens project demonstrates through corpus stylistics how computer-assisted methods can be used to study literary texts and lead to new insights into how readers perceive fictional characters. As part of the project we are developing the web app CLiC, designed specifically for the analysis of literary texts. CLiC Dickens started at the University of Nottingham in 2013, it is now a collaborative project with the University of Birmingham. 

CLiC code is divided into 2 halves, the python API server in ``server/`` and the HTML/Javascript client in ``client/``.

Documentation for CLiC is stored in ``docs/``.

For more information, cf. `CLiC Dickens - University of Birmingham <http://www.birmingham.ac.uk/schools/edacs/departments/englishlanguage/research/projects/clic.aspx/>`_.

Installation
------------

Clone this repository onto your computer, for example to install the latest stable version::

    git clone git@github.com:birmingham-ccr/clic /srv/clic --branch v2.1.2

Note that the directory name CLiC is cloned into is used for the systemd service name and NGINX configuration.
This allows multiple installations to live side-by-side, e.g. ``/srv/clic16`` and ``/srv/clic17`` will have systemd units ``clic16`` and ``clic17`` respectively.
All instructions assume you used ``clic``, if something else is used you will have to substitute.

Prerequisites
-------------

CLiC currently supports:

* Debian GNU/Linux 12 (bookworm) or later
* Ubuntu 24.04.1 LTS or later

Run the script to install the prerequisites from your system repositories as root::

    sudo ./prerequisites.sh

Configuration & compilation
---------------------------

Before building, you need to set your configuration.
Local configuration is stored in ``local-conf.mk``, the variables you can override are defined in ``conf.mk``.

For development, defaults should be sufficient and you can ignore ``local-conf.mk``, an empty file will be created.

For production, the following is a minimal example::

    cat <<EOF > local-conf.mk
    PROJECT_MODE = production
    WWW_SERVER_NAME = clic.bham.ac.uk
    WWW_SERVER_ALIASES = another.dns.name yet.another.dns.name
    GA_KEY = UA-XXXXX-Y
    EOF

``WWW_SERVER_NAME`` controls the DNS entry the web server responds to.

Download dependencies and compile both server/client by running::

    make

Next, run ``install.sh`` as root. This script automates the following steps:

* Create the postgres schema, and ensure the user that will run the API can access it (in development this is the user you used to check out the project).
* Configure systemd to launch the UWSGI process running CLiC, and start it if in production mode.
* Create / update an NGINX site config to use CLiC, and get NGINX to reload the config.

Each step is performed by the relevant ``*/install.sh`` script, and configured by make. Each can be inspected before running.

Run the install with the following::

    sudo ./install.sh

Populating the database
-----------------------

At this point CLiC can run, but there will be no content in the database.
CLiC content is stored in the `corpora repository <https://github.com/mahlberg-lab/corpora>`__,
to add or update this content run the import script::

    ./import.sh

As of 2024, this process takes approximately 20 minutes.

At this point CLiC should be ready for use. For more detail on various topics, see the `docs directory <docs/>`__.

SSL Certificates
----------------

At this point CLiC will be using an invalid cert. Run::

    sudo /usr/bin/dehydrated --register --accept-terms

...to register an account for CLiC, and::

    sudo /usr/bin/dehydrated -c

...to fetch a valid certificate.

In production mode, a cron-job will be created in ``/etc/cron.weekly/dehydrated`` to ensure this is kept up-to-date.

Acknowledgements
----------------

This work was supported by the Arts and Humanities Research Council grant reference AH/K005146/1
 
Please reference CLiC as the following:
 
Michaela Mahlberg, Peter Stockwell, Johan de Joode, Catherine Smith, Matthew Brook O’Donnell (forthcoming). “CLiC Dickens – Novel uses of concordances for the integration of corpus stylistics and cognitive poetics”, *Corpora*

This work is released under `MIT <LICENSE.rst>`__.
