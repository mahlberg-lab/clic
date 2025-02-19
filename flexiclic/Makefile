EGG_NAME=flexiclic
PYODIDE_VERSION=0.27.2
FLEXICONC_REPO=git@github.com:/fau-klue/flexiconc

PYODIDE_WHEELS = \
    jsonschema \
    pandas \

PREBUILT_WHEELS = \
    pypi/anytree-2.12.1-py3-none-any.whl \
    pypi/platformdirs-4.3.6-py3-none-any.whl \

LIBICU_WHEELS = \
    prebuilt/PyICU-2.14-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/icudata-76.1-py3-none-any.whl \

# NB: Need 3.8 for Numpy 2.0, thinc 9.0.0 is too new for 3.8.4
SPACY_WHEELS = \
    spacy-models/en_core_web_sm-3.8.0-py3-none-any.whl \
    spacy-pyodide/blis-0.7.11-cp312-cp312-pyodide_2024_0_wasm32.whl \
    spacy-pyodide/cymem-2.0.9a2-cp312-cp312-pyodide_2024_0_wasm32.whl \
    spacy-pyodide/murmurhash-1.0.10-cp312-cp312-pyodide_2024_0_wasm32.whl \
    spacy-pyodide/preshed-3.0.8-cp312-cp312-pyodide_2024_0_wasm32.whl \
    spacy-pyodide/thinc-8.2.3-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/spacy-3.8.4-cp312-cp312-pyodide_2024_0_wasm32.whl \
    prebuilt/srsly-2.4.8-cp312-cp312-pyodide_2024_0_wasm32.whl \
    pypi/catalogue-2.0.10-py3-none-any.whl \
    pypi/confection-0.1.5-py3-none-any.whl \
    pypi/wasabi-1.1.3-py3-none-any.whl \
    pypi/langcodes-3.5.0-py3-none-any.whl \
    pypi/tqdm-4.67.1-py3-none-any.whl \
    pypi/typer-0.15.1-py3-none-any.whl \
    pypi/click-8.1.8-py3-none-any.whl \
    pypi/weasel-0.4.1-py3-none-any.whl \

LOCAL_WHEELS = \
    flexiclic-0.0.0.dev0-py3-none-any.whl \
    FlexiConc-0.1.1.dev12-py3-none-any.whl \

OUT_FILES = \
    www/manifest.js \
    www/flexiclic.js \
    www/flexiclicWorker.js \
    www/pyodide-$(PYODIDE_VERSION)/pyodide.js \
    $(patsubst %, www/%, $(PREBUILT_WHEELS)) \
    $(patsubst %, www/%, $(LOCAL_WHEELS)) \

all: test $(OUT_FILES)

clean:
	rm -r www/* || true

bin/pip:
	python3 -m venv .

requirements.txt:
	touch requirements.txt

lib/.requirements: requirements.txt requirements-to-freeze.txt bin/pip flexiconc/setup.py
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
	@echo 'const PYODIDE_URL = `pyodide-$(PYODIDE_VERSION)/pyodide.js`' > www/manifest.js
	@echo 'const PRELOAD_WHEELS = `$(patsubst www/%, %, $(filter %.whl,$(OUT_FILES))) $(PYODIDE_WHEELS)`.trim().split(/\s+/)' >> www/manifest.js

www/flexiclic.js: flexiclic.js
	cp $^ $@

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

www/FlexiConc-%.whl: lib/.requirements flexiconc/setup.py flexiconc/*/*.py
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

# Fetch pyodide package
www/pyodide-$(PYODIDE_VERSION)/pyodide.js:
	mkdir -p www/pyodide-$(PYODIDE_VERSION)
	curl -L https://github.com/pyodide/pyodide/releases/download/$(PYODIDE_VERSION)/pyodide-$(PYODIDE_VERSION).tar.bz2 | tar -jxv --strip-components=1 -C www/pyodide-$(PYODIDE_VERSION)
	touch $@

.PHONY: all clean test www/manifest.js
