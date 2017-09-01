all: install test

install: lib/python2.7/site-packages/.requirements

bin/pip:
	/usr/bin/virtualenv .

lib/python2.7/site-packages/PyZ3950: bin/pip
	./bin/pip install http://www.panix.com/~asl2/software/PyZ3950/PyZ3950-2.04.tar.gz

./lib/python2.7/site-packages/ZSI: bin/pip
	svn checkout svn://svn.code.sf.net/p/pywebsvcs/code/branches/v1_5 /tmp/pywebsvcs-code
	mv /tmp/pywebsvcs-code/wstools /tmp/pywebsvcs-code/zsi/ZSI/wstools/
	./bin/pip install /tmp/pywebsvcs-code/zsi/
	rm -fr -- '/tmp/pywebsvcs-code'

lib/python2.7/site-packages/.requirements: requirements.txt bin/pip lib/python2.7/site-packages/PyZ3950 lib/python2.7/site-packages/ZSI
	./bin/pip install -r requirements.txt
	touch lib/python2.7/site-packages/.requirements

start:
	PYTHONPATH=. ./bin/python -m clic.web

clean:
	rm -rf -- ./bin ./include ./lib ./local ./share
	find ./clic -name '*.pyc' -exec rm -- {} \;

test: lib/python2.7/site-packages/.requirements
	./bin/py.test tests/

.PHONY: install test start
