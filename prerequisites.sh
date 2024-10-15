#!/bin/sh
set -eu

# shellcheck source=/dev/null
. /etc/os-release

if [ "$ID" = "debian" ] && [ "$VERSION_ID" -lt "12" ]; then
    echo "Unsupported debian version ${PRETTY_NAME}, add support to prerequisites.sh"
    exit 1
fi

if [ "$ID" = "ubuntu" ]; then
    BARE_VER="$(echo "${VERSION_ID}" | sed -e 's/.[0-9][0-9]//')"
    if [ "$BARE_VER" -lt "24" ]; then
        echo "Unsupported ubuntu version ${PRETTY_NAME}, add support to prerequisites.sh"
        exit 1
    fi
fi

if [ "$ID" = "debian" ] || [ "$ID" = "ubuntu" ]; then
    apt update

    # Server prerequisites
    apt install -y \
        postgresql postgresql-contrib libpq-dev \
        python3 python3-venv python3-dev \
        libicu-dev pkg-config \
    # NB: ICU needs to at least be version 56, postgresql at least version 9.5

    # Client prerequisites
    apt install -y make nodejs npm nginx

    # If you require web traffic to be encrypted (read: production)
    apt install -y dehydrated ssl-cert

    exit 0
fi

[ -n "${PRETTY_NAME}" ] && echo "Unknown operating system ${PRETTY_NAME}, add support to prerequisites.sh"
exit 1
