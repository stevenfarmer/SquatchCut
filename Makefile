PYTHON3 ?= python3
VENV_PYTHON := .venv/bin/python
PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(VENV_PYTHON),python)
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

.PHONY: setup-env
setup-env:
	$(PYTHON3) -m venv .venv
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PYTHON) -m pip install -r requirements-dev.txt

.PHONY: lint
lint:
	$(PYTHON) -m ruff check freecad/SquatchCut tests

.PHONY: format
format:
	$(PYTHON) -m ruff format freecad/SquatchCut tests

.PHONY: check-all
check-all: lint test-cov
