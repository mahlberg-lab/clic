EGG_NAME=flexiclic
PYODIDE_VERSION=0.27.2
FLEXICONC_REPO=git@github.com:/fau-klue/flexiconc

PYODIDE_WHEELS = \
    micropip \
    pyodide-http \
    jsonschema \
    pandas \

PREBUILT_WHEELS = \
    pypi/anytree-2.12.1-py3-none-any.whl \
    pypi/platformdirs-4.3.6-py3-none-any.whl \

LIBICU_WHEELS = \
    prebuilt/pyicu-2.14-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/icudata-76.1-py3-none-any.whl \

SPACY_MODELS = \
    spacy-models/en_core_web_md-3.8.0-py3-none-any.whl \
    spacy-models/en_core_web_sm-3.8.0-py3-none-any.whl \

# NB: Need 3.8 for Numpy 2.0, thinc 9.0.0 is too new for 3.8.4
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

LOCAL_WHEELS = \
    flexiclic-0.0.0.dev0-py3-none-any.whl \
    flexiconc-0.1.3-py3-none-any.whl \

OUT_FILES = \
    www/manifest.js \
    www/flexiclicWorker.js \
    www/pyodide-$(PYODIDE_VERSION)/pyodide.js \
    $(patsubst %, www/%, $(PREBUILT_WHEELS)) \
    $(patsubst %, www/%, $(LIBICU_WHEELS)) \
    $(patsubst %, www/%, $(SPACY_WHEELS)) \
    $(patsubst %, www/%, $(SPACY_MODELS)) \
    $(patsubst %, www/%, $(LOCAL_WHEELS)) \

all: test $(OUT_FILES)

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
	@echo 'const PYODIDE_REQUIREMENTS = {' > www/manifest.js
	@echo ' "_pyodide": `pyodide-$(PYODIDE_VERSION)/pyodide.js`,' >> www/manifest.js
	@echo ' "_preload": `$(LOCAL_WHEELS) $(PREBUILT_WHEELS) $(PYODIDE_WHEELS)`.trim().split(/\s+/),' >> www/manifest.js
	@echo ' "pyicu": `$(LIBICU_WHEELS)`.trim().split(/\s+/),' >> www/manifest.js
	@echo ' "spacy": `$(SPACY_WHEELS)`.trim().split(/\s+/),' >> www/manifest.js
	@for m in $(SPACY_MODELS); do echo ' "'$$(basename $$m -3.8.0-py3-none-any.whl)'": "'$$m'".trim().split(/\s+/),'; done >> www/manifest.js
	@echo '};' >> www/manifest.js
	@echo 'const SPACY_MODELS = [' >> www/manifest.js
	@for m in $(SPACY_MODELS); do echo ' "'$$(basename $$m -3.8.0-py3-none-any.whl)'",'; done >> www/manifest.js
	@echo '];' >> www/manifest.js

www/flexiclicWorker.js: flexiclicWorker.js
	cp $^ $@

www/flexiclic-%.whl: lib/.requirements flexiclic/*.py *.py pyproject.toml
	./bin/python3 -m build
	rm www/flexiclic-*.whl || true  # Remove old wheels to avoid version confusion
	cp dist/$(notdir $@) $@

flexiconc/setup.py:
	# TODO: Depend on flexiconc/*/*.py?
	[ -d "flexiconc/" ] && git -C flexiconc pull || git clone $(FLEXICONC_REPO) flexiconc
	# TODO: This should instead be -e flexiconc[optional]
	# ./bin/pip install -r flexiconc/optional_requirements.txt
	touch $@

www/flexiconc-%.whl: lib/.requirements flexiconc/setup.py flexiconc/*/*.py
	rm -r flexiconc/dist/ || true
	cd flexiconc && ../bin/python3 -m build
	rm www/FlexiConc-*.whl || true  # Remove old wheels to avoid version confusion
	cp flexiconc/dist/$(notdir $@) $@

www/prebuilt/%.whl:
	mkdir -p www/prebuilt/
	cp build-workdir/*/dist/$(notdir $@) www/prebuilt/

# Fetch pure-python packages direct from PyPI
www/pypi/%.whl:
	mkdir -p www/pypi
	# https://wiki.debian.org/debian/watch#PyPI
	(cd www/pypi/ && wget -c https://pypi.debian.net/`echo $(notdir $@) | sed 's/-.*//'`/$(notdir $@))

www/spacy-pyodide/%.whl:
	[ -d spacy-pyodide ] || git clone --depth 1 https://github.com/liu-nlp/spacy-pyodide
	mkdir -p www/spacy-pyodide/
	cp spacy-pyodide/$(notdir $@) $@

www/spacy-models/%.whl:
	mkdir -p www/spacy-models/
	(cd www/spacy-models/ && wget -c https://github.com/explosion/spacy-models/releases/download/$(subst -py3-none-any.whl,,$(notdir $@))/$(notdir $@))

www/spacy-models/%.tar.gz:
	mkdir -p www/spacy-models/
	(cd www/spacy-models/ && wget -c https://github.com/explosion/spacy-models/releases/download/$(subst .tar.gz,,$(notdir $@))/$(notdir $@))

# Fetch pyodide package
www/pyodide-$(PYODIDE_VERSION)/pyodide.js:
	mkdir -p www/pyodide-$(PYODIDE_VERSION)
	curl -L https://github.com/pyodide/pyodide/releases/download/$(PYODIDE_VERSION)/pyodide-$(PYODIDE_VERSION).tar.bz2 | tar -jxv --strip-components=1 -C www/pyodide-$(PYODIDE_VERSION)
	touch $@

.PHONY: all clean test www/manifest.js
