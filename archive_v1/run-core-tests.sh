#!/usr/bin/env bash
# @codex
# File: run-core-tests.sh
# Summary: Convenience script to run SquatchCut core tests with coverage.
# Details:
#   - Invokes pytest against core modules.
#   - Emits coverage for SquatchCut.core.nesting and session_state with a term report.
set -e
pytest --cov=SquatchCut.core.nesting --cov=SquatchCut.core.session_state --cov-report=term-missing
