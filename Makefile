TESTS = $(wildcard test/test_*.py)

.PHONY: test pep8

pep8:
	pep8 $(wildcard *.py) $(wildcard test/*.py)

test:
	@ $(foreach TEST,$(TESTS), \
		( \
			echo === Running test: $(TEST); \
			python $(TEST) || exit 1 \
		))
