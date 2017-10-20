#!/bin/sh
set -ex

# This script will create a systemd unit for running CLiC uWSGI, and
# an nginx config.
#
# It is tested on Debian, but should hopefully work on anything systemd-based.

[ -e ".local-conf" ] && . ./.local-conf

# ---------------------------
# Config options, to override any of these, set them in .local.conf

CLIC_PATH="${CLIC_PATH-$(dirname "$(readlink -f "$0")")}"
SERVER_NAME="${SERVER_NAME-$(hostname --fqdn)}"
SERVICE_NAME="${SERVICE_NAME-clic}"
SERVICE_FILE="${SERVICE_FILE-/etc/systemd/system/${SERVICE_NAME}.service}"
UWSGI_BIN="${UWSGI_BIN-${CLIC_PATH}/server/bin/uwsgi}"
UWSGI_USER="${UWSGI_USER-nobody}"
UWSGI_GROUP="${UWSGI_GROUP-nogroup}"
UWSGI_SOCKET="${UWSGI_SOCKET-/tmp/${SERVICE_NAME}_uwsgi.${CLIC_MODE}.sock}"
UWSGI_TIMEOUT="${UWSGI_TIMEOUT-5m}"
UWSGI_PROCESSES="${UWSGI_PROCESSES-4}"
UWSGI_THREADS="${UWSGI_THREADS-4}"
UWSGI_API_CACHE_TIME="${UWSGI_API_CACHE_TIME-60m}"
UWSGI_HARAKIRI="${UWSGI_HARAKIRI-0}"
UWSGI_CACHE_SIZE="${UWSGI_CACHE_SIZE-1g}"
[ "${CLIC_MODE}" = "production" ] && UWSGI_CACHE_ZONE="${UWSGI_CACHE_ZONE-api_cache}" || UWSGI_CACHE_ZONE="${UWSGI_CACHE_ZONE-off}"
GA_KEY="${GA_KEY-}"  # NB: This is used by the makefile, not here

set | grep -E 'CLIC|UWSGI|SERVICE'

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
    --harakiri ${UWSGI_HARAKIRI} \
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

mkdir -p ${CLIC_PATH}/uwsgi_cache
rm -- "${CLIC_PATH}/uwsgi_cache/*" || true
chown ${UWSGI_USER} ${CLIC_PATH}/uwsgi_cache

cat <<EOF > /etc/nginx/sites-available/${SERVICE_NAME}
upstream uwsgi_server {
    server unix://${UWSGI_SOCKET};
}

uwsgi_cache_path ${CLIC_PATH}/uwsgi_cache levels=1:2 keys_zone=api_cache:8m inactive=24h max_size=${UWSGI_CACHE_SIZE};

server {
    listen      80;
    server_name ${SERVER_NAME};
    charset     utf-8;
    root "${CLIC_PATH}/client/www";

    proxy_intercept_errors on;
    error_page 502 503 504 /error/bad_gateway.json;

    # Emergency CLiC disabling rewrite rule, uncomment to disable clic access
    # rewrite ^(.*) /error/maintenance.html;

    # Versioned resources can be cached forever
    location ~ ^(.*)\.r\w+\$ {
        try_files \$1 =404;
        expires 30d;
        add_header Vary Accept-Encoding;
    }

    location / {
        # Downloads links
        rewrite ^/downloads/clic-1.4.zip https://github.com/birmingham-ccr/clic-legacy/archive/4370f90a753763c9c3cff50549fa3446ef650954.zip permanent;
        rewrite ^/downloads/DNOV.zip https://github.com/birmingham-ccr/clic-DNOV-xml/archive/ac4ab0ca857fc0c53899ad60af4d116252f89555.zip permanent;
        rewrite ^/downloads/19C.zip https://github.com/birmingham-ccr/clic-19C-xml/archive/afde3a8a21ce3689dd7dd4f1b6271eb2724c2783.zip permanent;
        rewrite ^/downloads/clic-annotation.zip https://github.com/birmingham-ccr/clic/tree/ddd9d08b8078186426fd2e253665a59e8d4a161a/annotation permanent;
        rewrite ^/downloads/clic-gold-standard.zip https://github.com/birmingham-ccr/clic-gold-standard/archive/df4ff05f18d03103cd0ad561c1ff105d49ed30c1.zip permanent;

        # Caching for static resources
        expires 1m;
    }

    # We're a single-page-app, all URLs lead to index.html
    location ~ ^/[0-9a-zA-Z_-]+\$ {
        rewrite ^/downloads$ http://www.birmingham.ac.uk/schools/edacs/departments/englishlanguage/research/projects/clic/downloads.aspx;
        rewrite ^/concordances$ /concordance permanent;

        try_files \$uri \$uri.html /index.html;
    }

    location /api/ {
        include uwsgi_params;
        uwsgi_pass  uwsgi_server;
        uwsgi_read_timeout ${UWSGI_TIMEOUT};

        # All API results are deterministic, cache them
        uwsgi_cache ${UWSGI_CACHE_ZONE};
        uwsgi_cache_key \$uri?\$args;
        uwsgi_cache_valid 200 302 ${UWSGI_API_CACHE_TIME};
        expires ${UWSGI_API_CACHE_TIME};
    }
}
EOF
ln -fs /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/${SERVICE_NAME}
nginx -t
systemctl reload nginx.service
