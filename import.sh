#!/bin/sh
set -eu
cd "$(dirname "$(readlink -f "$0")")"

# Create / update a local copy of the corpora repository
[ -d corpora ] || git clone https://github.com/mahlberg-lab/corpora corpora
git -C corpora pull

# Update all content in parallel
find corpora/* -maxdepth 0 -type d -print0 | xargs -0 -P4 -n1 \
    ./server/bin/import_corpora_repo
