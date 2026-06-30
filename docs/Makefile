SHELL=/bin/bash -o pipefail
EGG_NAME=clic

SPHINXOPTS    =
SPHINXBUILD   = ./bin/sphinx-build
PAPER         =
BUILDDIR      = $(CURDIR)/_build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

all: clean compile

clean:
	rm -r -- _build module/*.rst || true

include ../conf.mk

compile: _build/.buildinfo

test:

lint:

coverage:

start:

install:

bin/pip:
	# 3.13+ adds "--without-scm-ignore-files", without which we blat .gitignore
	if python3 -m venv --help | grep -q -- "--without-scm-ignore-files"; then python3 -m venv --without-scm-ignore-files . ; else python3 -m venv .; fi

requirements.txt:
	touch requirements.txt

lib/.requirements: requirements.txt requirements-to-freeze.txt bin/pip
	# Install frozen requirements
	./bin/pip install -r requirements.txt
	# Make sure any new requirements are available
	./bin/pip install -r requirements-to-freeze.txt
	# Freeze the output at current state
	./bin/pip freeze | grep -v egg=$(EGG_NAME)  | grep -v 'pkg-resources==0.0.0' > requirements.txt
	touch lib/.requirements

_build/.buildinfo: lib/.requirements *.rst clicanalysis/*.rst advanced/*.rst policies/*.rst
	$(SPHINXBUILD) -b dirhtml $(ALLSPHINXOPTS) $(BUILDDIR)/
	$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) $(BUILDDIR)/latex

pdf: _build/.buildinfo
	(cd $(BUILDDIR)/latex && make)

.PHONY: compile test lint coverage start install _build/.buildinfo
