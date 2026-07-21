EGG_NAME=jsclictagger
PYODIDE_VERSION=0.27.2
CLICTAGGER_VERSION=0.9.1.dev0

# ## Layout
#
# Like flexiclic/, this Makefile assembles a www/ tree that a static web
# server can host.  The web worker (jsclictaggerWorker.js) downloads pyodide
# plus the wheels listed under PRELOAD_WHEELS, then imports jsclictagger and
# offers its methods to the page.
#
# Wheels can have one of three prefixes:
#   prebuilt/           — fetched from https://github.com/mahlberg-lab/prebuilt-wheels
#                         (used for compiled wasm wheels: pyicu, icudata)
#   pypi/               — pure-python wheels fetched from PyPI
#   pyodide-<version>/  — wheels pre-bundled with the current Pyodide release

###############################################################################
# Pyodide packages preloaded by loadPyodide() (need no separate fetch)
PRELOAD_PYODIDE = \
    micropip \

# Wheels micropip installs after loadPyodide() finishes
PRELOAD_WHEELS = \
    prebuilt/pyicu-2.14-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/icudata-76.1-py3-none-any.whl \
    pypi/Unidecode-1.3.8-py3-none-any.whl \
    clictagger-$(CLICTAGGER_VERSION)-py3-none-any.whl \
    jsclictagger-0.0.0.dev0-py3-none-any.whl \

###############################################################################
OUT_FILES = \
    www/manifest.js \
    www/jsclictaggerWorker.js \
    www/pyodide-$(PYODIDE_VERSION)/pyodide.js \
    $(subst .whl,.whl.gz,$(patsubst %, www/%, $(PRELOAD_WHEELS))) \

all: test $(OUT_FILES)

compile: $(OUT_FILES)

clean:
	rm -fr -- clictagger || true
	rm -r dist/* || true
	rm -r www/* || true
	rm -r .venv || true

.venv/bin/pip:
	python3 -m venv .venv

requirements.txt:
	touch requirements.txt

.venv/lib/.requirements: requirements.txt requirements-to-freeze.txt .venv/bin/pip setup.py pyproject.toml
	# clictagger isn't pip-installable from PyPI as a wheel — install
	# whichever version we're going to ship from the local source tree
	[ -d "clictagger" ] || git clone https://github.com/mahlberg-lab/clictagger
	.venv/bin/pip install ./clictagger || true
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -r requirements-to-freeze.txt
	.venv/bin/pip freeze | grep -v egg=$(EGG_NAME) | grep -vE '^pkg-resources=|^setuptools=|^wheel=|^clictagger @' > requirements.txt
	touch .venv/lib/.requirements

test: .venv/lib/.requirements
	# TODO: .venv/bin/pytest $(EGG_NAME) tests

www/manifest.js:
	mkdir -p www/
	@echo 'const PYODIDE_REQUIREMENTS = {' > www/manifest.js
	@echo ' "_pyodide": `pyodide-$(PYODIDE_VERSION)/pyodide.js`,' >> www/manifest.js
	@echo ' "_preload_pyodide": `$(PRELOAD_PYODIDE)`.trim().split(/\s+/),' >> www/manifest.js
	@echo ' "_preload_wheels": `$(PRELOAD_WHEELS)`.trim().split(/\s+/),' >> www/manifest.js
	@echo '};' >> www/manifest.js

www/jsclictaggerWorker.js: jsclictaggerWorker.js
	mkdir -p www/
	cp $^ $@

# Build our wrapper wheel
www/jsclictagger-%.whl.gz: .venv/lib/.requirements jsclictagger/*.py pyproject.toml setup.py
	mkdir -p www/
	.venv/bin/python3 -m build
	rm www/jsclictagger-*.whl.gz 2>/dev/null || true
	gzip -c dist/$(subst .whl.gz,.whl,$(notdir $@)) > $@

# Build the clictagger wheel from the local source tree
www/clictagger-%.whl.gz: .venv/lib/.requirements $(shell find ./clictagger -name '*.py' 2>/dev/null)
	mkdir -p www/
	[ -d "clictagger" ] || git clone https://github.com/mahlberg-lab/clictagger
	rm -r ./clictagger/dist/ 2>/dev/null || true
	cd ./clictagger && $(CURDIR)/.venv/bin/python3 -m build --wheel
	rm www/clictagger-*.whl.gz 2>/dev/null || true
	gzip -c ./clictagger/dist/$(subst .whl.gz,.whl,$(notdir $@)) > $@

# Pre-built wasm wheels from the mahlberg-lab/prebuilt-wheels repo
www/prebuilt/%.whl.gz:
	[ -d prebuilt-wheels ] && git -C prebuilt-wheels pull || git clone --depth 1 https://github.com/mahlberg-lab/prebuilt-wheels
	mkdir -p www/prebuilt/
	gzip -c prebuilt-wheels/$(subst .whl.gz,.whl,$(notdir $@)) > $@

# Pure-python wheels fetched straight from PyPI
www/pypi/%.whl.gz:
	mkdir -p www/pypi
	# https://wiki.debian.org/debian/watch#PyPI
	(cd www/pypi/ && wget -c https://pypi.debian.net/`echo $(notdir $@) | sed 's/-.*//'`/$(subst .whl.gz,.whl,$(notdir $@)))
	gzip -f $(subst .whl.gz,.whl,$@)

# Fetch the pyodide runtime itself
www/pyodide-$(PYODIDE_VERSION)/pyodide.js:
	mkdir -p www/pyodide-$(PYODIDE_VERSION)
	curl -L https://github.com/pyodide/pyodide/releases/download/$(PYODIDE_VERSION)/pyodide-$(PYODIDE_VERSION).tar.bz2 \
	    | tar -jxv --strip-components=1 -C www/pyodide-$(PYODIDE_VERSION)
	for f in www/pyodide-$(PYODIDE_VERSION)/*.whl ; do echo $$f ; gzip -f $$f; done
	for f in www/pyodide-$(PYODIDE_VERSION)/*.wasm ; do echo $$f ; gzip -f $$f; done
	touch $@

.PHONY: all clean compile test www/manifest.js
