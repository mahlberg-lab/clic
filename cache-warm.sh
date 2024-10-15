#!/bin/sh
# cache-warm.sh: Make sure that critical CLiC API URLs are cached
#
# Usage:
#   ./cache-warm (URL of CLiC server)
set -eu

HOST="$1" ; shift

for ENDPOINT in \
        /api/corpora/image?corpora=corpus%3ADNov \
        /api/corpora/image?corpora=corpus%3A19C \
        /api/corpora/image?corpora=corpus%3AChiLit \
        /api/corpora/image?corpora=corpus%3AArTs \
        /api/corpora/image?corpora=corpus%3AAAW \
        /api/corpora/headlines \
        /api/corpora
do
    echo -n "=== ${HOST}${ENDPOINT}" 1>&2
    # Make pre-warm attempts
    for i in 1 2 3
    do
        echo -n " [${i}]"
        curl -k -s -I -X GET "${HOST}${ENDPOINT}" >/dev/null
    done
    echo

    # Final attempt should be cached, if not stop
    curl -k -s -I -X GET "${HOST}${ENDPOINT}" | tee /dev/stderr | grep -q 'X-Uwsgi-Cached: HIT' || {
        echo "*** Caching failed!" 1>&2
        exit 1
    }
done
