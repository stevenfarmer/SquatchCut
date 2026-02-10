#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x .venv/bin/python ]]; then
  echo "ERROR: .venv does not exist. Run \"make setup-env\" before committing."
  exit 1
fi

PRE_COMMIT_HOME="$(pwd)/.cache/pre-commit"
mkdir -p "$PRE_COMMIT_HOME"
export PRE_COMMIT_HOME

if [[ "${SKIP_DEP_INSTALL:-0}" != "1" ]]; then
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/pip install -r requirements-dev.txt
else
  echo "Skipping dependency install (SKIP_DEP_INSTALL=1)."
fi

.venv/bin/ruff check .
if [[ "${SKIP_MYPY:-0}" != "1" ]]; then
  if [[ ! -x .venv/bin/mypy ]]; then
    echo "ERROR: mypy is not installed in .venv. Run with SKIP_MYPY=1 to bypass or install requirements-dev.txt."
    exit 1
  fi
  PYTHONPATH=freecad .venv/bin/mypy freecad/SquatchCut
else
  echo "Skipping mypy (SKIP_MYPY=1)."
fi
PYTHONPATH=freecad .venv/bin/python -m pytest \
  --cov=SquatchCut.core.nesting \
  --cov=SquatchCut.core.session_state \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-fail-under=80
