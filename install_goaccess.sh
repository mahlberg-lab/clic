#!/bin/sh
set -eu
PROJECT_PATH="${PROJECT_PATH-$(dirname "$(readlink -f "$0")")}"  # The full project path, e.g. /srv/x
PROJECT_NAME="${PROJECT_NAME-$(basename ${PROJECT_PATH})}"  # The project directory name, e.g. x

GOACCESS_UNIT_NAME="${PROJECT_NAME}-goaccess"
GOACCESS_OUTPUT_DIR="${PROJECT_PATH}/goaccess_www"
GOACCESS_MAXMIND_DB_TAR="$(ls -1 /srv/clic/GeoLite2-Country*.tar.gz)"

apt -y --no-install-recommends install goaccess

mkdir -p ${GOACCESS_OUTPUT_DIR}
# Project user should own it, "adm" (i.e. the DynamicUser) can write to it
chown "$(stat -c '%U' ${PROJECT_PATH}/.git):adm" ${GOACCESS_OUTPUT_DIR}
chmod g+w ${GOACCESS_OUTPUT_DIR}

ls -l /etc/goaccess/browsers.list  # Ensure it exists in package
mkdir -p /etc/goaccess
tar -C /etc/goaccess --strip-components=1 -zxf ${GOACCESS_MAXMIND_DB_TAR} $(basename "${GOACCESS_MAXMIND_DB_TAR}" .tar.gz)/GeoLite2-Country.mmdb
cat <<EOF > /etc/goaccess/${PROJECT_NAME}.conf
log-format COMBINED

agent-list true
with-output-resolver false
http-method no
http-protocol no
no-query-string true
no-term-resolver false

anonymize-ip true

all-static-files true
browsers-file /etc/goaccess/browsers.list
double-decode true

hide-referrer *.google.com
hide-referrer bing.com
ignore-crawlers true

ignore-status 400

real-os true

static-file .css
static-file .js
static-file .jpg
static-file .png
static-file .gif
static-file .ico
static-file .map
static-file .jpeg
static-file .json
static-file .zip
static-file .wasm
static-file .svg
static-file .whl

geoip-database /etc/goaccess/GeoLite2-Country.mmdb
EOF

cat <<EOF > "/etc/systemd/system/${GOACCESS_UNIT_NAME}.service"
[Unit]
Description=GoAccess Live Log Analyzer

[Service]
Type=oneshot
# Make per-year persistence directories, symlink current year to cur, for use below
ExecStart=/bin/sh -c 'mkdir -p "/var/lib/%N/\$(date +%%Y)" && ln -frs "/var/lib/%N/\$(date +%%Y)" "/var/lib/%N/cur"'
ExecStart=/usr/bin/goaccess \
    --config-file="/etc/goaccess/${PROJECT_NAME}.conf" \
    --db-path "/var/lib/%N/cur" --persist --restore \
    /var/log/nginx/clic_api.access.log \
    -o "${GOACCESS_OUTPUT_DIR}/report.html"
# Copy report output to per-year report
ExecStart=/bin/sh -c 'cp ${GOACCESS_OUTPUT_DIR}/report.html ${GOACCESS_OUTPUT_DIR}/report-\$(date +%%Y).html'
# Create /var/lib/%N
StateDirectory=%N

DynamicUser=yes
SupplementaryGroups=adm
ReadWriteDirectories=${GOACCESS_OUTPUT_DIR}
EOF

cat <<EOF > "/etc/systemd/system/${GOACCESS_UNIT_NAME}.timer"
[Unit]
Description=Generate goaccess reports every 10 minutes
Requires=${GOACCESS_UNIT_NAME}.service

[Timer]
Unit=${GOACCESS_UNIT_NAME}.service
OnBootSec=1min
OnUnitActiveSec=10min

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl start "${GOACCESS_UNIT_NAME}.service"
systemctl enable "${GOACCESS_UNIT_NAME}.timer"
systemctl start "${GOACCESS_UNIT_NAME}.timer"
