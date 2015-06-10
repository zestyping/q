TESTS = $(wildcard test/test_*.py)

.PHONY: deps pep8 test build push clean

all: pep8 test build

deps:
	# q doesn't have any *runtime* dependencies.
	# These dependencies are only needed for development.
	pip install pep8
	pip install wheel

pep8:
	@echo === Running pep8 on files
	pep8 $(wildcard *.py) $(wildcard test/*.py)

test:
	@echo
	@ $(foreach TEST,$(TESTS), \
		( \
			echo === Running test: $(TEST); \
			python $(TEST) || exit 1 \
		))

build:
	python setup.py sdist
	python setup.py bdist_wheel

push: build
	python setup.py sdist upload
	python setup.py bdist_wheel upload

clean:
	rm -rf build dist q.egg-info
	find -name *.pyc -delete
	@- git status
