SUBDIRS = $(shell ls -d */)

compile: clic_revision
	for dir in client server; do make -C $$dir $@; done

test: clic_revision
	for dir in client server; do make -C $$dir $@; done

start: clic_revision
	for dir in client server; do make -C $$dir $@; done

clic_revision: .git/logs/HEAD
	(git describe --exact-match HEAD 2>/dev/null || echo $$(git rev-parse --abbrev-ref HEAD):$$(git rev-parse --short HEAD) ) > $@.mktmp
	mv $@.mktmp $@

.PHONY: compile start
