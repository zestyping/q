TESTS = $(wildcard test/test_*.py)

.PHONY: test pep8

all: pep8 test push

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

push:
	# Try the builds first
	python setup.py sdist
	python setup.py bdist_wheel
	# Upload the packages
	python setup.py sdist upload
	python setup.py bdist_wheel upload
