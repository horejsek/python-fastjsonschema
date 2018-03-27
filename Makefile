
all:
	@echo "make install - Install on local system"
	@echo "make test - Run tests during development"
	@echo "make performance - Run performance test of this and other implementation"
	@echo "make doc - Make documentation"
	@echo "make clean - Get rid of scratch and byte files"


deb:
	python3 setup.py --command-packages=stdeb.command bdist_deb

upload:
	python3 setup.py register sdist upload

install:
	pip install --editable .[test]

test:
	python3 -m pytest tests

performance:
	python3 performance.py

doc:
	cd docs; make

clean:
	python3 setup.py clean
	find . -name '*.pyc' -delete
