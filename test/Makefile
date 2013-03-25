TESTS = $(wildcard test_*.py)

test:
	@- $(foreach TEST,$(TESTS), \
		echo === Running test: $(TEST); \
		python $(TEST); \
		)
