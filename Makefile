SUBDIRS = $(shell ls -d */)

compile:
	for dir in client server; do make -C $$dir $@; done

test:
	for dir in client server; do make -C $$dir $@; done

lint:
	for dir in client server; do make -C $$dir $@; done

start:
	for dir in client server; do make -C $$dir $@; done

.PHONY: compile test lint start
