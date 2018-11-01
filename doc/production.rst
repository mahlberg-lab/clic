Managing a production instance of CLiC
======================================

Installation instructions are all in `README.rst <../README.rst>`__.

Note that the directory name CLiC is cloned into is used for the systemd service name and NGINX configuration.
This allows multiple installations to live side-by-side, e.g. ``/srv/clic16`` and ``/srv/clic17`` will have systemd units ``clic16`` and ``clic17`` respectively.
The below assumes you used ``clic``, if something else is used you will have to substitute.

Start / stop the CLiC service
-----------------------------

If you need to stop/start CLiC outside this for whatever reason, use systemctl,
e.g. ``systemctl stop clic``.

To see the current status, use ``systemctl status clic``.

Troubleshooting
---------------

If you see the NGINX default "Welcome to nginx!" page when trying to use CLiC from a web browser:

* Make sure you used a ``WWW_SERVER_NAME`` that resolves to the CLiC server in ``local-conf.mk``. Re-run ``make`` and ``./install.sh``.
* Make sure NGINX started without errors: ``systemctl status -ln50 nginx``

If any CLiC query responds with the error "The CLiC server did not respond, the query may have taken too long.":

* Make sure that CLiC is started with ``systemctl start clic``.

If you see the "CLiC is down for maintenance" page:

* Make sure CLiC has started without errors: ``systemctl status -ln50 clic``

If you see errors about missing tables, or queries are particularly slow:

* Postgres may need vacuuming. Run ``sudo -upostgres psql -c "VACUUM ANALYSE" bham_clic_db``.
