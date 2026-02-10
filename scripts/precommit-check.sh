#!/usr/bin/env bash
set -euo pipefail

if [[ ! -x .venv/bin/python ]]; then
  echo "ERROR: .venv does not exist. Run \"make setup-env\" before committing."
  exit 1
fi

PRE_COMMIT_HOME="$(pwd)/.cache/pre-commit"
mkdir -p "$PRE_COMMIT_HOME"
export PRE_COMMIT_HOME

.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements-dev.txt

.venv/bin/ruff check .
PYTHONPATH=freecad .venv/bin/mypy freecad/SquatchCut
PYTHONPATH=freecad .venv/bin/python -m pytest \
  --cov=SquatchCut.core.nesting \
  --cov=SquatchCut.core.session_state \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-fail-under=80
