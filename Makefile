SUBDIRS = $(shell ls -d */)

compile:
	for dir in schema client server; do make -C $$dir $@; done

test:
	for dir in schema client server; do make -C $$dir $@; done

lint:
	for dir in schema client server; do make -C $$dir $@; done

coverage:
	for dir in schema client server; do make -C $$dir $@; done

start:
	for dir in schema client server; do make -C $$dir $@; done

deploy/deploy.sh:
	for dir in schema client server; do make -C $$dir $@; done

.PHONY: compile test lint coverage start deploy/deploy.sh
