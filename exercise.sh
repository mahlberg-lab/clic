#!/bin/bash
# exercise.sh: Simple end-to-end testing for CLiC
#
# Usage:
#   ./exercise.sh [--monitor] (URL of CLiC server) (exercise output files ...)
#
# * URL of CLiC server: Which server to test, e.g. http://clic.bham.ac.uk
#
# * exercise output files: A set of files to test. Normally exercise_outputs/*.
#   The first line of each exercise_outputs file is a URL to fetch from the server,
#   and below that is the output of "time /usr/bin/curl" when fetching that URL.
#   On running this script, the files are re-written. Use "git diff" to see changes.
#
# * --monitor Switches to monitoring mode. In this case, excercise_outputs files
#   are not updated with new content. If the output varies dramatically from the
#   saved copy, a diff is shown to stdout and the script fails. Otherwise, the script
#   will show no output and result in success
set -euo pipefail

# Lines to ignore when monitoring output
FILTER_OUTPUT='^(real|user|sys)\s+|"version":{'

MONITOR=""
[ $1 = "--monitor" ] && { MONITOR="1"; shift; }
HOST="$1" ; shift
[ $# -ge 1 ] && TESTS=($*) || TESTS=(./exercise_outputs/*)

for f in "${TESTS[@]}"; do
    [ -n "${MONITOR}" ] && OUTPUT=/tmp/exercise.sh.tmp || OUTPUT="$f"
    ENDPOINT="$(head -n 1 $f)"
    [ -z "${MONITOR}" ] && echo "$f: $HOST$ENDPOINT"

    echo $ENDPOINT > "${OUTPUT}"
    echo "" > "/tmp/exercise.sh.$(basename ${OUTPUT}).err"
    # NB: POST to disable caching
    { time /usr/bin/curl -X POST -sS "$HOST$ENDPOINT" | sed -E 's/,$//g ; s/\\n/ /g ; s/\\u[0-9a-f]+/'"'"'/g' | sort -dib; } >> ${OUTPUT} 2>>/tmp/exercise.sh.$(basename ${OUTPUT}).err
    cat /tmp/exercise.sh.$(basename ${OUTPUT}).err >> ${OUTPUT}
    rm /tmp/exercise.sh.$(basename ${OUTPUT}).err

    if [ -n "${MONITOR}" ]; then
        diff -u \
            <(cat $f | grep -vE ${FILTER_OUTPUT}) \
            <(cat ${OUTPUT} | grep -vE ${FILTER_OUTPUT})
        rm -- "${OUTPUT}"
    fi
done
