#!/bin/bash
set -euo pipefail

HOST="$1" ; shift
[ $# -ge 1 ] && TESTS=($*) || TESTS=(./exercise_outputs/*)

for f in "${TESTS[@]}"; do
    ENDPOINT="$(head -n 1 $f)"
    echo $f: $HOST$ENDPOINT
    {
        echo $ENDPOINT
        time /usr/bin/curl -s "$HOST$ENDPOINT"
        echo
    } > $f 2>&1 | tee -a $f
    echo
done
