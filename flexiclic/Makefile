EGG_NAME=flexiclic
PYODIDE_VERSION=0.27.2
FLEXICONC_REPO=git@github.com:/fau-klue/flexiconc

# ## Making packages available
#
# When a FlexiConc algorithm declares a requirement, e.g. ``"requires": ["pyicu"]``,
# and a set of packages is defined in manifest.js, flexiclicWorker.js will try to
# download it. This set of packages does not have to be purely python dependencies,
# and could be model data, e.g.
#
# 1. Define a new x_WHEELS variable with required wheels. Wheels can have a prefix of:
#   ``prebuilt/``: Fetched from https://github.com/mahlberg-lab/prebuilt-wheels (see that repository to add further wheels)
#   ``pypi/``: Fetched from PyPI, for "*-none-any.whl" pure python wheels
#   ``pyodide-$(PYODIDE_VERSION)/``: Pre-bundled in the current pyodide version
# 2. Add x_WHEELS to the OUT_FILES list
# 3. Add a definition for x_WHEELS to the manifest.js section below

###############################################################################
# _preload: wheels to preload when launching web worker
PRELOAD_PYODIDE = \
    micropip \
    pyodide-http \
    jsonschema \
    pandas \

PRELOAD_WHEELS = \
    pypi/anytree-2.12.1-py3-none-any.whl \
    pypi/platformdirs-4.3.6-py3-none-any.whl \
    flexiclic-0.0.0.dev0-py3-none-any.whl \
    flexiconc-0.1.3-py3-none-any.whl \

###############################################################################
# pyicu: Wheels loaded when importing pyicu
PYICU_WHEELS = \
    prebuilt/pyicu-2.14-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/icudata-76.1-py3-none-any.whl \

###############################################################################
# spacy: Wheels loaded when importing spacy
SPACY_WHEELS = \
    prebuilt/spacy-3.8.4-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/srsly-2.5.1-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/thinc-8.3.4-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/blis-1.2.0-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/cymem-2.0.11-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/murmurhash-1.0.12-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/preshed-3.0.9-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/marisa_trie-1.2.1-cp312-cp312-pyodide_2024_0_wasm32.whl \
    pypi/catalogue-2.0.10-py3-none-any.whl \
    pypi/confection-0.1.5-py3-none-any.whl \
    pypi/wasabi-1.1.3-py3-none-any.whl \
    pypi/langcodes-3.5.0-py3-none-any.whl \
    pypi/tqdm-4.67.1-py3-none-any.whl \
    pypi/typer-0.15.2-py3-none-any.whl \
    pypi/click-8.1.8-py3-none-any.whl \
    pypi/weasel-0.4.1-py3-none-any.whl \

###############################################################################
# Wheels for each spacy model, will be loaded by name
SPACY_MODELS = \
    spacy-models/en_core_web_md-3.8.0-py3-none-any.whl \
    spacy-models/en_core_web_sm-3.8.0-py3-none-any.whl \

###############################################################################
OUT_FILES = \
    www/manifest.js \
    www/flexiclicWorker.js \
    www/pyodide-$(PYODIDE_VERSION)/pyodide.js \
    $(subst .whl,.whl.gz,$(patsubst %, www/%, $(PRELOAD_WHEELS))) \
    $(subst .whl,.whl.gz,$(patsubst %, www/%, $(PYICU_WHEELS))) \
    $(subst .whl,.whl.gz,$(patsubst %, www/%, $(SPACY_WHEELS))) \
    $(subst .whl,.whl.gz,$(patsubst %, www/%, $(SPACY_MODELS))) \

all: test $(OUT_FILES)

compile: $(OUT_FILES)

clean:
	rm -r www/* || true

bin/pip:
	python3 -m venv .

requirements.txt:
	touch requirements.txt

lib/.requirements: requirements.txt requirements-to-freeze.txt bin/pip flexiconc/setup.py setup.py pyproject.toml
	# Install frozen requirements
	./bin/pip install -r requirements.txt
	# Make sure any new requirements are available
	./bin/pip install -r requirements-to-freeze.txt
	# Freeze the output at current state
	./bin/pip freeze | grep -v egg=$(EGG_NAME) | grep -vE '^pkg-resources=|^setuptools=|^wheel=' > requirements.txt
	touch lib/.requirements

test: lib/.requirements
	./bin/pytest $(EGG_NAME) tests

www/manifest.js:
	mkdir -p www/
	@echo 'const PYODIDE_REQUIREMENTS = {' > www/manifest.js
	@echo ' "_pyodide": `pyodide-$(PYODIDE_VERSION)/pyodide.js`,' >> www/manifest.js
	@echo ' "_preload": `$(PRELOAD_PYODIDE) $(PRELOAD_WHEELS)`.trim().split(/\s+/),' >> www/manifest.js
	@echo ' "pyicu": `$(PYICU_WHEELS)`.trim().split(/\s+/),' >> www/manifest.js
	@echo ' "spacy": `$(SPACY_WHEELS)`.trim().split(/\s+/),' >> www/manifest.js
	# Make requirements entry for model name --> wheel
	@for m in $(SPACY_MODELS); do echo ' "'$$(basename $$m -3.8.0-py3-none-any.whl)'": "'$$m'".trim().split(/\s+/),'; done >> www/manifest.js
	@echo '};' >> www/manifest.js
	# Make list of all available models
	@echo 'const SPACY_MODELS = [' >> www/manifest.js
	@for m in $(SPACY_MODELS); do echo ' "'$$(basename $$m -3.8.0-py3-none-any.whl)'",'; done >> www/manifest.js
	@echo '];' >> www/manifest.js

www/flexiclicWorker.js: flexiclicWorker.js
	mkdir -p www/
	cp $^ $@

www/flexiclic-%.whl.gz: lib/.requirements flexiclic/*.py *.py pyproject.toml
	mkdir -p www/
	./bin/python3 -m build
	rm www/flexiclic-*.whl.gz || true  # Remove old wheels to avoid version confusion
	gzip -c dist/$(subst .whl.gz,.whl,$(notdir $@)) > $@

flexiconc/setup.py:
	[ -d "flexiconc/" ] && git -C flexiconc pull || git clone $(FLEXICONC_REPO) flexiconc
	touch $@

www/flexiconc-%.whl.gz: $(shell find flexiconc -type f -name '*.py' || true)
	mkdir -p www/
	rm -r flexiconc/dist/ || true
	cd flexiconc && ../bin/python3 -m build
	rm www/FlexiConc-*.whl.gz || true  # Remove old wheels to avoid version confusion
	gzip -c flexiconc/dist/$(subst .whl.gz,.whl,$(notdir $@)) > $@

www/prebuilt/%.whl.gz:
	[ -d prebuilt-wheels ] && git -C prebuilt-wheels pull || git clone --depth 1 https://github.com/mahlberg-lab/prebuilt-wheels
	mkdir -p www/prebuilt/
	gzip -c prebuilt-wheels/$(subst .whl.gz,.whl,$(notdir $@)) > $@

# Fetch pure-python packages direct from PyPI
www/pypi/%.whl.gz:
	mkdir -p www/pypi
	# https://wiki.debian.org/debian/watch#PyPI
	(cd www/pypi/ && wget -c https://pypi.debian.net/`echo $(notdir $@) | sed 's/-.*//'`/$(subst .whl.gz,.whl,$(notdir $@)))
	gzip -f $(subst .whl.gz,.whl,$@)

www/spacy-models/%.whl.gz:
	mkdir -p www/spacy-models/
	(cd www/spacy-models/ && wget -c https://github.com/explosion/spacy-models/releases/download/$(subst -py3-none-any.whl.gz,,$(notdir $@))/$(subst .whl.gz,.whl,$(notdir $@)))
	gzip -f $(subst .whl.gz,.whl,$@)

www/spacy-models/%.tar.gz:
	mkdir -p www/spacy-models/
	(cd www/spacy-models/ && wget -c https://github.com/explosion/spacy-models/releases/download/$(subst .tar.gz,,$(notdir $@))/$(notdir $@))

# Fetch pyodide package
www/pyodide-$(PYODIDE_VERSION)/pyodide.js:
	mkdir -p www/pyodide-$(PYODIDE_VERSION)
	curl -L https://github.com/pyodide/pyodide/releases/download/$(PYODIDE_VERSION)/pyodide-$(PYODIDE_VERSION).tar.bz2 | tar -jxv --strip-components=1 -C www/pyodide-$(PYODIDE_VERSION)
	for f in www/pyodide-$(PYODIDE_VERSION)/*.whl ; do echo $$f ; gzip -f $$f; done
	for f in www/pyodide-$(PYODIDE_VERSION)/*.wasm ; do echo $$f ; gzip -f $$f; done
	touch $@

.PHONY: all clean test www/manifest.js
