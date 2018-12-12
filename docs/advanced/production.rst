Managing a production instance of CLiC
======================================

Installation instructions are all in `README.rst <../README.rst>`__.
For a production system, you are likely to want to install a particular release, e.g.::

    git clone git://github.com/birmingham-ccr/clic /srv/clic
    git checkout v1.7.0

Note that the directory name CLiC is cloned into is used for the systemd service name and NGINX configuration.
This allows multiple installations to live side-by-side, e.g. ``/srv/clic16`` and ``/srv/clic17`` will have systemd units ``clic16`` and ``clic17`` respectively.
The below assumes you used ``clic``, if something else is used you will have to substitute.

Database performance tweaking
-----------------------------

Default settings for Postgres will result in a working CLiC, but it's suggested to tweak the following:

* ``work_mem``: The amount of memory which can be used for sorts. ``60MB`` handles the worst likely queries but will use potentially an extra 1G of server memory.

Start / stop the CLiC service
-----------------------------

If you need to stop/start CLiC outside this for whatever reason, use systemctl,
e.g. ``systemctl stop clic``.

To see the current status, use ``systemctl status clic``.

Upgrading a CLiC instance
-------------------------

To upgrade a CLiC instance, first check out the code for the given release, e.g.::

    git fetch && git checkout v1.7.0

...then run::

    make
    sudo ./install.sh

Troubleshooting
---------------

Logs are available with: ``journalctl -S-1d -uclic``.

If you see the NGINX default "Welcome to nginx!" page when trying to use CLiC from a web browser:

* Make sure you used a ``WWW_SERVER_NAME`` that resolves to the CLiC server in ``local-conf.mk``. Re-run ``make`` and ``./install.sh``.
* Make sure NGINX started without errors: ``systemctl status -ln50 nginx``

If any CLiC query responds with the error "The CLiC server did not respond, the query may have taken too long.":

* Make sure that CLiC is started with ``systemctl start clic``.
* Any error messages are cached by NGINX and your web browser briefly, clear your cache and try again. You can also re-run ``./install.sh`` to clear the NGINX cache.

If you see the "CLiC is down for maintenance" page:

* Make sure CLiC has started without errors: ``systemctl status -ln50 clic``

If you see errors about missing tables, or queries are particularly slow:

* Postgres may need vacuuming. Run ``sudo -upostgres psql -c "VACUUM ANALYSE" clic_db``.

If the home page is particularly slow:

The homepage entries aren't cached yet, reload the page ~3 times until it is.

Back-up / generating dumps
--------------------------

An import process from the raw text files can take some time.
Instead, it can be more efficent to dump/restore a database from another CLiC
instance.

Dump the database with the following::

    ./schema/bin/db_dump clic.dump

Restore with the following. NB: **this will destroy all existing data**::

    ./schema/bin/db_restore clic.dump

If you do not want to destroy the existing database, you could set a new database name in ``local-conf.mk``::

    echo "DB_NAME = my_new_clic_database" >> local-conf.mk

...and then re-run ``make`` before restoring.

There are server options to speed up the restore, see `this blog post <http://www.databasesoup.com/2014/09/settings-for-fast-pgrestore.html>`__.
