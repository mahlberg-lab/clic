#!/bin/sh
set -ex

# This script will create a systemd unit for running CLiC uWSGI, and
# an nginx config.
#
# It is tested on Debian, but should hopefully work on anything systemd-based.

# ---------------------------
# Config options, to override any of these, set them in .local.conf
CLIC_MODE="${CLIC_MODE-development}" # or "production"
CLIC_PATH="$(dirname "$(readlink -f "$0")")"
SERVER_NAME="$(hostname --fqdn)"
SERVICE_NAME="clic"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
UWSGI_BIN="${CLIC_PATH}/server/bin/uwsgi"
UWSGI_USER="nobody"
UWSGI_GROUP="nogroup"
UWSGI_SOCKET=/tmp/${SERVICE_NAME}_uwsgi.${CLIC_MODE}.sock
UWSGI_TIMEOUT="5m"
UWSGI_PROCESSES="4"
UWSGI_THREADS="4"

[ -e "${CLIC_PATH}/.local-conf" ] && . "${CLIC_PATH}/.local-conf" 

# ---------------------------
# Ownership of server config / cache files

[ -f "${CLIC_PATH}/server/clic-chapter-cache.pickle" ] || touch "${CLIC_PATH}/server/clic-chapter-cache.pickle"
chown ${UWSGI_USER} "${CLIC_PATH}/server/clic-chapter-cache.pickle"
chmod g+w "${CLIC_PATH}/server/clic-chapter-cache.pickle"

# ---------------------------
# Systemd unit file to run uWSGI

systemctl | grep -q "${SERVICE_NAME}.service" && systemctl stop ${SERVICE_NAME}.service
cat <<EOF > ${SERVICE_FILE}
[Unit]
Description=uWSGI daemon for ${SERVICE_NAME}
After=network.target

[Service]
ExecStart=${UWSGI_BIN} \
    --master \
    --processes=${UWSGI_PROCESSES} --threads=${UWSGI_THREADS} \
    --enable-threads --thunder-lock \
    --mount /=clic.web:app \
    --chmod-socket=666 \
    -s ${UWSGI_SOCKET}
WorkingDirectory=${CLIC_PATH}/server
User=${UWSGI_USER}
Group=${UWSGI_GROUP}

[Install]
WantedBy=multi-user.target
EOF

if [ "${CLIC_MODE}" = "production" ]; then
    [ -f "${UWSGI_SOCKET}" ] && chown ${UWSGI_USER}:${UWSGI_GROUP} "${UWSGI_SOCKET}"
    systemctl enable ${SERVICE_NAME}.service
    systemctl start ${SERVICE_NAME}.service
else
    systemctl disable ${SERVICE_NAME}.service
    systemctl stop ${SERVICE_NAME}.service
fi

# ---------------------------
# NGINX config for serving clientside

cat <<EOF > /etc/nginx/sites-available/${SERVICE_NAME}
upstream uwsgi_server {
    server unix://${UWSGI_SOCKET};
}

server {
    listen      80;
    server_name bham-clic.clifford.shuttlethread.com;
    charset     utf-8;
    root "${CLIC_PATH}/client/www";

    proxy_intercept_errors on;
    error_page 502 503 504 /error/maintenance.html;

    # Emergency CLiC disabling rewrite rule, uncomment to disable clic access
    # rewrite ^(.*) /error/maintenance.html;

    # Alias some page names
    location / {
        rewrite ^/\$ /concordance permanent;
        rewrite ^/concordances\$ /concordance permanent;
        rewrite ^/subsets\$ /subset permanent;
        rewrite ^/keyword\$ /keyword permanent;
    }

    # We're a single-page-app, all URLs lead to index.html
    location ~ ^/[0-9a-zA-Z_-]+\$ {
        try_files \$uri /index.html;
    }

    location /api/ {
        include uwsgi_params;
        uwsgi_pass  uwsgi_server;
        uwsgi_read_timeout ${UWSGI_TIMEOUT};
    }
}
EOF
ln -fs /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/${SERVICE_NAME}
systemctl reload nginx.service
