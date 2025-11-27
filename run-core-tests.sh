#!/usr/bin/env bash
# @codex
# File: run-core-tests.sh
# Summary: Convenience script to run SquatchCut core tests with coverage.
# Details:
#   - Invokes pytest against core modules.
#   - Emits coverage for SquatchCut/core with term report.
set -e
pytest --cov=SquatchCut/core --cov-report=term-missing
