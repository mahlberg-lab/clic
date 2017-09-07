SUBDIRS = $(shell ls -d */)

compile:
	for dir in server client; do make -B -C $$dir $@; done

start:
	for dir in server; do make -B -C $$dir $@; done

.PHONY: compile start
