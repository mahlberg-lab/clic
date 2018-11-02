#!/bin/sh
set -eux

[ "${1-}" = "--recreate" ] && { DB_RECREATE="x"; shift; } || DB_RECREATE=""
[ "$#" -gt "1" ] || { echo "Usage: $0 [--recreate] (db_name) (db_user) [db_pass]" 1>&2; exit 1; }
DB_NAME="$1"
DB_USER="$2"
DB_PASS="${3-}"
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

# If DB_PASS set, we're probably using network socket/password auth
# otherwise, assume UNIX socket, ident
[ -n "${DB_PASS}" ] && PASSWD_OPT="'${DB_PASS}'" || PASSWD_OPT="NULL"
echo "=============== Create DB user"
${PSQL} ${DB_NAME} -f - <<EOF
DO
\$do\$
BEGIN
   IF NOT EXISTS (SELECT
                  FROM pg_catalog.pg_roles
                  WHERE rolname = '${DB_USER}') THEN
      CREATE ROLE "${DB_USER}" LOGIN PASSWORD ${PASSWD_OPT};
   END IF;
END
\$do\$;
COMMIT;
EOF

echo "=============== Grant roles"
${PSQL} ${DB_NAME} -f - <<EOF
BEGIN;
GRANT CONNECT ON DATABASE ${DB_NAME} TO "${DB_USER}";
GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public
    TO "${DB_USER}";
GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public
    TO "${DB_USER}";
ALTER DEFAULT PRIVILEGES
    IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "${DB_USER}";
COMMIT;
EOF
