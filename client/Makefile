GIT = git
NODE = node
NODE != which node || which nodejs
NODE_CMD = NODE_PATH="$(CURDIR)" $(NODE)
SHELL=/bin/bash -o pipefail

OUTPUTS := index

all: test lint compile

include ../conf.mk

OUT_FILES = \
    www/js/polyfill.min.js \
    www/js/libraries.min.js \
    www/css/libraries.min.css \
    www/css/chosen-sprite.png \
    $(foreach O,$(OUTPUTS),www/$(O).html www/js/$(O).min.js www/css/$(O).min.css)

LIBRARIES_JS = \
    chosen-js \
    datatables.net \
    jquery/dist/jquery.slim.js \
    cookieconsent \
    nouislider \
    unidecode \
    @codemirror/state \
    @codemirror/view \

LIBRARIES_CSS = \
    node_modules/chosen-js/chosen.css \
    node_modules/tom-select/dist/css/tom-select.default.css \
    node_modules/nouislider/dist/nouislider.min.css \
    node_modules/cookieconsent/build/cookieconsent.min.css \
    node_modules/bootstrap/dist/css/bootstrap-reboot.min.css

compile: node_modules/.requirements clean-unused $(OUT_FILES)

start: all

install:
	./install.sh

test: node_modules/.requirements
	$(NODE_CMD) node_modules/.bin/tape tests/test_*.{js,mjs}

coverage: node_modules/.requirements
	$(NODE_CMD) node_modules/istanbul/lib/cli.js cover node_modules/tape/bin/tape tests/test_*.js
	mkdir -p ../client/www/coverage
	ln -frs coverage/lcov-report ../client/www/coverage/client
	echo Visit http://$(WWW_SERVER_NAME)/coverage/client/index.html

lint: node_modules/.requirements
	$(NODE_CMD) node_modules/xo/dist/cli.js

clean:
	rm -r -- "node_modules/" || true
	git ls-files --others www/ | xargs -r rm --

clean-unused:
	for f in $(filter-out \
	    $(foreach f,$(OUT_FILES),$(shell dirname $(f))/$(shell readlink $(f))), \
	    $(wildcard www/*/*.min.r*.*) \
	); do rm -- $$f; done

watch:
	while inotifywait -r lib; do make compile; done

node_modules/.requirements: package.json package-lock.json
	npm ci
	touch $@

# Move minified output to a version with sha1 hash in it's name, symlink to proper output
sha1_symlink = \
    REV_FILE="www/$(1)/$$(basename $(3) .min.$(1)).min.r$$(sha1sum $(2) | head -c7).$(1)"; \
    mv $(2) $$REV_FILE; \
    ln -rsf $$REV_FILE $(3)

# Generate environment variables that point to the sha1 hash version
sha1_envvars = \
    for f in $(1); do \
        eval sha_$$(basename $$f | sed 's/\W/_/g')=$$(readlink $$f); \
    done;

www/css/chosen-sprite.png: node_modules/chosen-js/chosen-sprite.png
	mkdir -p $(dir $@)
	cp node_modules/chosen-js/chosen-sprite*.png www/css/

www/js/libraries.min.js: package.json build/esbuild.js
	mkdir -p $(dir $@)
	(cd www/js && ln -sf ../../node_modules .)
	rm -f $@
	$(NODE_CMD) build/esbuild.js libraries $@ $(LIBRARIES_JS)
	$(call sha1_symlink,js,$@,$@)

www/css/libraries.min.css: package.json
	mkdir -p $(dir $@)
	(cd www/css && ln -sf ../../lib .)
	cat $(LIBRARIES_CSS) > $@.mktmp
	$(call sha1_symlink,css,$@.mktmp,$@)

www/js/%.min.js: lib/%.js lib/*.js lib/*.mjs package.json build/esbuild.js
	mkdir -p $(dir $@)
	(cd www/js && ln -sf ../../lib .)
	rm -f $@ $@.map
	$(NODE_CMD) build/esbuild.js main $< $@ $(LIBRARIES_JS)
	$(call sha1_symlink,js,$@,$@)

www/css/%.min.css: lib/%.css lib/*.css package.json
	mkdir -p $(dir $@)
	(cd www/css && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/.bin/postcss \
	    --config postcss.config.js \
	    -o $@ \
	    $<
	$(call sha1_symlink,css,$@,$@)

www/%.html: lib/%.html lib/controlbar.html $(filter-out %.html,$(OUT_FILES)) \
    $(PROJECT_PATH)/conf.mk \
    build/html_compile.js \
    package.json
	set -a; \
	    $(call sha1_envvars,$(OUT_FILES)) \
	    NODE_PATH="$(CURDIR)" $(NODE) build/html_compile.js $< $@.mktmp $^
	mv $@.mktmp $@

.PHONY: compile test coverage start install lint clean clean-unused watch
