set -eu

# Build DB
sudo -u "${DB_SUDO_USER}" ./build.sh "${DB_NAME}" "${DB_USER}" "${DB_PASS}"
