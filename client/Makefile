GIT = git
NPM = npm
YARN = yarn
NODE = node
NODE != which node || which nodejs
NODE_PATH = node_modules
NODE_CMD = NODE_PATH="$(NODE_PATH)" $(NODE)
OUT_FILES = \
    www/js/bundle.clic.min.js \
    www/js/bundle.chapter.min.js \
    www/js/bundle.libraries.min.js \
    www/css/bundle.libraries.min.css \
    www/chapter.html \
    www/index.html

BUNDLE_LIBS = \
    chosen-js \
    custom-event-polyfill \
    datatables.net \
    jquery/dist/jquery.slim.js \
    nouislider \


all: test lint compile

start: all

pre_commit: lint compile

compile: $(NODE_PATH) $(OUT_FILES)

$(NODE_PATH): package.json
	NODE_PATH="$(NODE_PATH)" $(YARN)
	touch $(NODE_PATH)

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

www/js/bundle.clic.min.js: package.json lib/*
	mkdir -p www/js
	(cd www/js && ln -sf ../../lib .)
	(cd www/js && ln -sf ../../node_modules .)
	$(NODE_CMD) $(NODE_PATH)/browserify/bin/cmd.js --debug \
	        $(foreach l,$(BUNDLE_LIBS),-x $(l)) \
	        -g uglifyify \
	        lib/index.js \
	    | $(NODE_CMD) $(NODE_PATH)/exorcist/bin/exorcist.js $@.map \
	        --base . \
	        --root /js/ \
	        --url /js/$(notdir $@).map \
	    > $@.mktmp
	mv $@.mktmp $@

www/js/bundle.chapter.min.js: package.json lib/*
	mkdir -p www/js
	(cd www/js && ln -sf ../../lib .)
	(cd www/js && ln -sf ../../node_modules .)
	$(NODE_CMD) $(NODE_PATH)/browserify/bin/cmd.js --debug \
	        $(foreach l,$(BUNDLE_LIBS),-x $(l)) \
	        -g uglifyify \
	        lib/index-chapter.js \
	    | $(NODE_CMD) $(NODE_PATH)/exorcist/bin/exorcist.js $@.map \
	        --base . \
	        --root /js/ \
	        --url /js/$(notdir $@).map \
	    > $@.mktmp
	mv $@.mktmp $@

www/js/bundle.libraries.min.js: package.json
	mkdir -p www/js
	$(NODE_CMD) $(NODE_PATH)/browserify/bin/cmd.js \
	        $(foreach l,$(BUNDLE_LIBS),-r $(l)) \
	        -g uglifyify \
	    > $@.mktmp
	mv $@.mktmp $@

www/css/bundle.libraries.min.css: package.json \
    node_modules/chosen-js/chosen.css \
    node_modules/nouislider/distribute/nouislider.min.css \
    node_modules/bootstrap/dist/css/bootstrap-reboot.min.css
	mkdir -p www/css
	cat $^ > $@.mktmp
	cp node_modules/chosen-js/chosen-sprite*.png www/css/
	mv $@.mktmp $@

www/%.html: html/%.html \
    build/html_compile.js \
    www/css/clic.*.css \
    www/js/*.js \
    ../.local-conf \
    package.json
	CURRENT_REV=
	[ -e "../.local-conf" ] && \
	    . ../.local-conf; \
	    export GA_KEY; \
	    export CUR_REV="`git describe --exact-match HEAD 2>/dev/null || echo $$(git rev-parse --abbrev-ref HEAD):$$(git rev-parse --short HEAD)`"; \
	    $(NODE_CMD) build/html_compile.js \
	        $< > $@.mktmp
	mv $@.mktmp $@

.PHONY: pre_commit compile test start browser_test lint clean
