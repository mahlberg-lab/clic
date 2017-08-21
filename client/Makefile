GIT = git
NPM = npm
YARN = yarn
NODE = node
NODE != which node || which nodejs
NODE_PATH = node_modules
NODE_CMD = NODE_PATH="$(NODE_PATH)" $(NODE)
OUT_FILES = \
    www/js/bundle.clic.min.js \
    www/css/bundle.libraries.min.css \


all: test lint compile

pre_commit: lint compile

compile: $(OUT_FILES)

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
	(cd www/js && ln -sf ../../lib .)
	(cd www/js && ln -sf ../../node_modules .)
	$(NODE_CMD) $(NODE_PATH)/browserify/bin/cmd.js --debug \
	        -x ace-editor \
	        -g uglifyify \
	        lib/index.js \
	    | $(NODE_CMD) $(NODE_PATH)/exorcist/bin/exorcist.js $@.map \
	        --base . \
	        --root /js/ \
	        --url /js/$(notdir $@).map \
	    > $@.mktmp
	mv $@.mktmp $@

www/css/bundle.libraries.min.css: package.json \
    node_modules/bootstrap/dist/css/bootstrap.min.css
	cat $^ > $@.mktmp
	mv $@.mktmp $@

.PHONY: pre_commit compile test browser_test lint clean
