set -eu

cat <<EOF > ${DB_CONF_FILE}
# Created by $0, do not edit
work_mem = ${DB_CONF_WORK_MEM}
EOF

# Build DB
sudo -u "${DB_SUDO_USER}" ./build.sh "${DB_NAME}" "${DB_USER}" "${DB_PASS}"

/etc/init.d/postgresql reload
