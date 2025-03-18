set -eu

cat <<EOF > ${DB_CONF_FILE}
# Created by $0, do not edit
work_mem = ${DB_CONF_WORK_MEM}

# The Postgresql JIT is currently adding seconds to any concordance query
jit = off
EOF

# Build DB
sudo -u "${DB_SUDO_USER}" ./build.sh "${DB_NAME}"

# Create user(s)
[ -n "${DB_USER}" ] && sudo -u "${DB_SUDO_USER}" ./user.sh "${DB_NAME}" "${DB_USER}" "${DB_PASS}"
[ -n "${DB_ALT_USER}" ] && sudo -u "${DB_SUDO_USER}" ./user.sh "${DB_NAME}" "${DB_ALT_USER}" "${DB_ALT_PASS}"

/etc/init.d/postgresql reload
