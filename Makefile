SUBDIRS = $(shell ls -d */)

compile:
	for dir in server client; do make -C $$dir $@; done

start:
	for dir in server; do make -C $$dir $@; done

.PHONY: compile start
