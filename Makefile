TESTS = $(wildcard test/test_*.py)

.PHONY: deps pycodestyle test build push clean

all: pycodestyle test build

deps:
	# q doesn't have any *runtime* dependencies.
	# These dependencies are only needed for development.
	pip install pycodestyle
	pip install wheel

pycodestyle:
	@echo === Running pycodestyle on files
	pycodestyle $(wildcard *.py) $(wildcard test/*.py)

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
