"""@codex
Entry point to run SquatchCut FreeCAD integration tests via pytest.
Used by run-freecad-tests.sh / freecadcmd -c "import run_freecad_tests".
"""

"""
Entry point for running integration tests under FreeCAD.

Usage (from the repo root):

    freecadcmd -c "import run_freecad_tests"

This will run pytest on tests_integration/.
"""

import sys
from pathlib import Path

# Ensure the repository root (directory containing this file) is on sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest


def main() -> int:
    """Run integration tests under FreeCAD's Python and return pytest's exit code."""
    args = ["tests_integration"]
    return pytest.main(args)


# When executed via freecadcmd import, run immediately and propagate exit code.
raise SystemExit(main())
