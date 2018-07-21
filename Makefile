.PHONY: all venv test lint lint-js lint-web test test-web watch compile run makemessages compilemessages clean-dev deb
SHELL=/bin/bash

VENV_NAME?=venv
VENV_BIN=$(shell pwd)/${VENV_NAME}/bin

PYTHON=${VENV_BIN}/python3


all:
	@echo "make test - Run tests during development"
	@echo "make performance - Run performance test of this and other implementation"
	@echo "make doc - Make documentation"
	@echo "make clean - Get rid of scratch and byte files"


venv: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: setup.py
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	# Some problem in latest version of setuptools during extracting translations.
	${PYTHON} -m pip install -U pip setuptools==39.1.0
	${PYTHON} -m pip install -e .[devel]
	touch $(VENV_NAME)/bin/activate

test: venv
	${PYTHON} -m pytest
test-lf: venv
	${PYTHON} -m pytest --last-failed

lint: venv
	${PYTHON} -m pylint fastjsonschema

performance: venv
	${PYTHON} performance.py

doc:
	cd docs; make

upload: venv
	${PYTHON} setup.py register sdist upload

deb: venv
	${PYTHON} setup.py --command-packages=stdeb.command bdist_deb

clean:
	find . -name '*.pyc' -exec rm --force {} +
	rm -rf $(VENV_NAME) *.eggs *.egg-info dist build docs/_build .mypy_cache .cache
