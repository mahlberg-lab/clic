SHELL=/bin/bash -o pipefail
EGG_NAME=clic

SPHINXOPTS    =
PAPER         =
BUILDDIR      = $(CURDIR)/_build

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d $(BUILDDIR)/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .
# the i18n builder cannot share the environment and doctrees with the others
I18NSPHINXOPTS  = $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

all: compile

include ../conf.mk

compile: _build/.buildinfo

test:

lint:

coverage:

start:

_build/.buildinfo: *.rst */*.rst
	[ -d "./module" ] && rm -r -- ./module || mkdir ./module
	../server/bin/sphinx-apidoc -o module -e ../server/ \
	    '../server/appconfig.py' \
	    '../server/conftest.py' \
	    '../server/tests/*.py'
	../server/bin/sphinx-build -b dirhtml $(ALLSPHINXOPTS) $(BUILDDIR)/

.PHONY: compile test lint coverage start
