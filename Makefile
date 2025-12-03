PYTHON ?= python
TEST_PATH ?= tests
COV_TARGET ?= SquatchCut.core.nesting SquatchCut.core.session_state
COV_FAIL_UNDER ?= 80

# Base pytest command (without coverage)
PYTEST_CMD = $(PYTHON) -m pytest

# Coverage options
COV_OPTS = $(addprefix --cov=,$(COV_TARGET)) --cov-report=term-missing --cov-fail-under=$(COV_FAIL_UNDER)

.PHONY: test
test:
	$(PYTEST_CMD) $(TEST_PATH)

.PHONY: test-cov
test-cov:
	$(PYTEST_CMD) $(COV_OPTS) --cov-report=xml $(TEST_PATH)

.PHONY: lint
lint:
	$(PYTHON) -m ruff check SquatchCut tests

.PHONY: format
format:
	$(PYTHON) -m ruff format SquatchCut tests

.PHONY: check-all
check-all: lint test-cov
