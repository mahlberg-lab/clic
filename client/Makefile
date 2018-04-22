GIT = git
NPM = npm
YARN = yarn
NODE = node
NODE != which node || which nodejs
NODE_CMD = NODE_PATH="$(CURDIR)" $(NODE)
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

compile: node_modules/ $(OUT_FILES)

test: node_modules/
	TZ=Europe/London $(NODE_CMD) node_modules/tape/bin/tape tests/test_*.js

coverage: node_modules/
	$(NODE_CMD) node_modules/istanbul/lib/cli.js cover node_modules/tape/bin/tape tests/test_*.js

browser_test: node_modules/
	$(NODE_CMD) node_modules/browserify/bin/cmd.js --debug \
	    -x ace-editor \
	    tests/*.js \
	    | $(NODE_CMD) node_modules/testling/bin/cmd.js $(TESTLING_OPTS)

lint: node_modules/
	$(NODE_CMD) node_modules/jslint/bin/jslint lib/*.js tests/*.js

clean:
	rm -r -- "node_modules/"
	rm -- $(OUT_FILES)

watch:
	while inotifywait -r lib; do make compile; done

node_modules/: package.json yarn.lock
	$(YARN)
	touch node_modules/

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
	(cd www/css && ln -sf ../../lib .)
	cat $(LIBRARIES_CSS) > $@.mktmp
	mv $@.mktmp $@

www/js/%.min.js: lib/%.js lib/*.js package.json
	mkdir -p www/js
	(cd www/js && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/browserify/bin/cmd.js --debug \
	        $(foreach l,$(LIBRARIES_JS),-x $(l)) \
	        $< \
	    | $(NODE_CMD) node_modules/uglify-js/bin/uglifyjs \
	        --compress --mangle "reserved=['$$','require','exports']" \
	        --source-map "content='inline',url='$(notdir $@).map'" \
	        --output $@.mktmp
	mv $@.mktmp.map $@.map
	mv $@.mktmp $@

www/css/%.min.css: lib/%.css lib/*.css package.json
	mkdir -p www/css
	(cd www/css && ln -sf ../../lib .)
	$(NODE_CMD) node_modules/postcss-cli/bin/postcss \
	    --config postcss.config.js \
	    -o $@ \
	    $<

www/%.html: lib/%.html $(filter-out %.html,$(OUT_FILES)) \
    ../.local-conf \
    ../clic_revision \
    build/html_compile.js \
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
