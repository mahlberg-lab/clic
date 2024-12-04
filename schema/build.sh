#!/bin/sh
set -eux

[ "${1-}" = "--recreate" ] && { DB_RECREATE="x"; shift; } || DB_RECREATE=""
[ "$#" -gt "0" ] || { echo "Usage: $0 (db_name)" 1>&2; exit 1; }
DB_NAME="$1"
PSQL="psql -X --set ON_ERROR_STOP=1 --set AUTOCOMMIT=off"

# Drop and/or create database
if ${PSQL} -l | grep -q "${DB_NAME}"; then
    if [ -n "${DB_RECREATE}" ]; then
        echo "DROP DATABASE ${DB_NAME}" | ${PSQL} postgres
        createdb "${DB_NAME}"
    fi
else
    createdb "${DB_NAME}"
fi

# Run DB schemas
for s in "$(dirname $0)"/*.sql; do
    echo "=============== $s"
    ${PSQL} -a -f "$s" "${DB_NAME}"
done
