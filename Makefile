SUBDIRS = $(shell ls -d */)

compile:
	make -C schema $@
	make -C client $@
	make -C server $@
	make -C docs $@

test:
	make -C schema $@
	make -C client $@
	make -C server $@
	make -C docs $@

lint:
	make -C schema $@
	make -C client $@
	make -C server $@
	make -C docs $@

coverage:
	make -C schema $@
	make -C client $@
	make -C server $@
	make -C docs $@

start:
	make -C schema $@
	make -C client $@
	make -C server $@
	make -C docs $@

install:
	make -C schema $@
	make -C client $@
	make -C server $@
	make -C docs $@

.PHONY: compile test lint coverage start install
