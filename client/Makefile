GIT = git
YARN = yarn
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
    nouislider \
    unidecode \

LIBRARIES_CSS = \
    node_modules/chosen-js/chosen.css \
    node_modules/nouislider/distribute/nouislider.min.css \
    node_modules/bootstrap/dist/css/bootstrap-reboot.min.css

compile: node_modules/ clean-unused $(OUT_FILES) deploy/deploy.sh

start: all

test: node_modules/
	$(NODE_CMD) node_modules/.bin/tape tests/test_*.js

coverage: node_modules/
	$(NODE_CMD) node_modules/istanbul/lib/cli.js cover node_modules/tape/bin/tape tests/test_*.js

lint: node_modules/
	$(NODE_CMD) node_modules/jslint/bin/jslint */*.js

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

node_modules/: package.json yarn.lock
	$(YARN)
	touch node_modules/

yarn.lock:
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

www/js/libraries.min.js: package.json
	mkdir -p $(dir $@)
	(cd www/js && ln -sf ../../node_modules .)
	$(NODE_CMD) node_modules/.bin/browserify \
	        $(foreach l,$(LIBRARIES_JS),-r $(l)) \
	    | $(NODE_CMD) node_modules/.bin/uglifyjs \
	        --compress --mangle "reserved=['$$','require','exports']" \
	        --output $@.mktmp
	$(call sha1_symlink,js,$@.mktmp,$@)

www/css/libraries.min.css: package.json
	mkdir -p $(dir $@)
	(cd www/css && ln -sf ../../lib .)
	cat $(LIBRARIES_CSS) > $@.mktmp
	$(call sha1_symlink,css,$@.mktmp,$@)

www/js/%.min.js: lib/%.js lib/*.js package.json
	mkdir -p $(dir $@)
	(cd www/js && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/.bin/browserify --debug \
	        $(foreach l,$(LIBRARIES_JS),-x $(l)) \
	        $< \
	    | $(NODE_CMD) node_modules/.bin/uglifyjs \
	        --compress --mangle "reserved=['$$','require','exports']" \
	        --source-map "content='inline',url='$(notdir $@).map'" \
	        --output $@.mktmp
	mv $@.mktmp.map $@.map
	$(call sha1_symlink,js,$@.mktmp,$@)

www/css/%.min.css: lib/%.css lib/*.css package.json
	mkdir -p $(dir $@)
	(cd www/css && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/postcss-cli/bin/postcss \
	    --config postcss.config.js \
	    -o $@ \
	    $<
	$(call sha1_symlink,css,$@,$@)

www/%.html: lib/%.html $(filter-out %.html,$(OUT_FILES)) \
    $(PROJECT_PATH)/conf.mk \
    build/html_compile.js \
    package.json
	set -a; \
	    $(call sha1_envvars,$(OUT_FILES)) \
	    NODE_PATH="$(CURDIR)" $(NODE) build/html_compile.js $< $@.mktmp $^
	mv $@.mktmp $@

deploy/deploy.sh: $(PROJECT_PATH)/conf.mk deploy/generate.sh
	deploy/generate.sh

.PHONY: compile test start lint clean clean-unused watch
