"""@codex
Entry point to run SquatchCut FreeCAD integration tests via pytest.
Used by run-freecad-tests.sh / freecadcmd -c "import run_freecad_tests".

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

import pytest  # noqa: E402


def main() -> int:
    """Run integration tests under FreeCAD's Python and return pytest's exit code."""
    args = ["tests_integration"]
    return pytest.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
