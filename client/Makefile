GIT = git
NPM = npm
YARN = yarn
NODE = node
NODE != which node || which nodejs
NODE_PATH = node_modules
NODE_CMD = NODE_PATH="$(NODE_PATH)" $(NODE)
SHELL=/bin/bash -o pipefail

OUTPUTS := index chapter

OUT_FILES = \
    www/js/polyfill.min.js \
    www/js/libraries.min.js \
    www/css/libraries.min.css \
    www/css/chosen-sprite.png \
    $(foreach O,$(OUTPUTS),www/$(O).html www/js/$(O).min.js www/css/$(O).min.css)

LIBRARIES_JS = \
    chosen-js \
    custom-event-polyfill \
    datatables.net \
    jquery/dist/jquery.slim.js \
    nouislider \

LIBRARIES_CSS = \
    node_modules/chosen-js/chosen.css \
    node_modules/nouislider/distribute/nouislider.min.css \
    node_modules/bootstrap/dist/css/bootstrap-reboot.min.css

all: test lint compile

start: all

pre_commit: lint compile

compile: $(NODE_PATH) $(OUT_FILES)

test: $(NODE_PATH)
	TZ=Europe/London $(NODE_CMD) $(NODE_PATH)/tape/bin/tape tests/test_*.js

coverage: $(NODE_PATH)
	$(NODE_CMD) node_modules/istanbul/lib/cli.js cover $(NODE_PATH)/tape/bin/tape tests/test_*.js

browser_test: $(NODE_PATH)
	$(NODE_CMD) $(NODE_PATH)/browserify/bin/cmd.js --debug \
	    -x ace-editor \
	    tests/*.js \
	    | $(NODE_CMD) $(NODE_PATH)/testling/bin/cmd.js $(TESTLING_OPTS)

lint: $(NODE_PATH)
	$(NODE_CMD) $(NODE_PATH)/jslint/bin/jslint lib/*.js tests/*.js

clean:
	rm -r -- "$(NODE_PATH)"
	rm -- www/js/*.min.js www/css/*.min.css www/html/*.min.html www/index-md5sums.html

$(NODE_PATH): package.json yarn.lock
	NODE_PATH="$(NODE_PATH)" $(YARN)
	touch $(NODE_PATH)

yarn.lock:
	touch $@

www/css/chosen-sprite.png: node_modules/chosen-js/chosen-sprite.png
	mkdir -p www/css
	cp node_modules/chosen-js/chosen-sprite*.png www/css/

www/js/libraries.min.js: package.json
	mkdir -p www/js
	(cd www/js && ln -sf ../../node_modules .)
	$(NODE_CMD) node_modules/browserify/bin/cmd.js \
	        $(foreach l,$(LIBRARIES_JS),-r $(l)) \
	    | $(NODE_CMD) node_modules/uglify-js/bin/uglifyjs \
	        --compress --mangle "reserved=['$$','require','exports']" \
	        --output $@.mktmp
	mv $@.mktmp $@

www/css/libraries.min.css: package.json
	mkdir -p www/css
	(cd www/js && ln -sf ../../lib .)
	cat $(LIBRARIES_CSS) > $@.mktmp
	mv $@.mktmp $@

www/js/%.min.js: package.json lib/*.js
	mkdir -p www/js
	(cd www/js && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/browserify/bin/cmd.js --debug \
	        $(foreach l,$(LIBRARIES_JS),-x $(l)) \
	        lib/$(basename $(basename $(notdir $@))).js \
	    | $(NODE_CMD) node_modules/uglify-js/bin/uglifyjs \
	        --compress --mangle "reserved=['$$','require','exports']" \
	        --source-map "content='inline',url='$(notdir $@).map'" \
	        --output $@.mktmp
	mv $@.mktmp.map $@.map
	mv $@.mktmp $@

www/css/%.min.css: package.json lib/*.css
	mkdir -p www/css
	(cd www/js && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/postcss-cli/bin/postcss \
	    --config postcss.config.js \
	    -o $@ \
	    lib/$(basename $(basename $(notdir $@))).css

www/%.html: html/%.html ../clic_revision \
    build/html_compile.js \
    www/css/%.min.css \
    www/js/%.min.js \
    ../.local-conf \
    package.json
	CURRENT_REV=
	[ -e "../.local-conf" ] && \
	    . ../.local-conf; \
	    export GA_KEY; \
	    export CUR_REV="`cat ../clic_revision`"; \
	    $(NODE_CMD) build/html_compile.js \
	        $< > $@.mktmp
	mv $@.mktmp $@

.PHONY: pre_commit compile test start browser_test lint clean
