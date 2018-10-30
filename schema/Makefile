all: compile

include ../conf.mk

compile: deploy/deploy.sh

test: compile

lint:

start:

deploy/deploy.sh: $(PROJECT_PATH)/conf.mk deploy/generate.sh
	deploy/generate.sh

.PHONY: compile test lint start
