all: compile

include ../conf.mk

compile: bin/db_dump bin/db_restore

test: compile

lint:

start:

install:
	./install.sh

bin/db_dump: ../conf.mk
	@mkdir -p ./bin
	@/bin/echo -e \
'#!/bin/sh'\\n\
'sudo -u "$(DB_SUDO_USER)" pg_dump --format=c --no-owner "$(DB_NAME)" > $${1-clic.dump}'\\n\
	    > $@
	@chmod a+x $@

bin/db_restore: ../conf.mk
	@mkdir -p ./bin
	@/bin/echo -e \
'#!/bin/sh'\\n\
'set -e'\\n\
''\\n\
'systemctl stop $(PROJECT_NAME)'\\n\
''\\n\
'# NB: We dont use --clean --create since the DB_NAME in the dump might not be the one we want'\\n\
'sudo -u "$(DB_SUDO_USER)" dropdb "$(DB_NAME)" || true'\\n\
'sudo -u "$(DB_SUDO_USER)" createdb "$(DB_NAME)" '\\n\
'sudo -u "$(DB_SUDO_USER)" pg_restore --format=c -d "$(DB_NAME)" --verbose $${1-clic.dump}'\\n\
''\\n\
'# Re-run build.sh to make sure DB is sane'\\n\
'(cd $(PROJECT_PATH)/schema && '\\n\
'    sudo -u "$(DB_SUDO_USER)" ./build.sh "$(DB_NAME)" "$(DB_USER)" "$(DB_PASS)"; '\\n\
'    )'\\n\
	    > $@
	@chmod a+x $@

.PHONY: compile test lint start install
