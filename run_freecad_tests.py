"""@codex
Entry point to run SquatchCut FreeCAD integration tests via pytest.
Used by run-freecad-tests.sh / FreeCADCmd -c "import run_freecad_tests".
"""

"""
Entry point for running integration tests under FreeCAD.

Usage (from the repo root):

    FreeCADCmd -c "import run_freecad_tests"

This will run pytest on tests_integration/.
"""

import sys
from pathlib import Path

# Ensure the repository root (directory containing this file) is on sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest

if __name__ == "__main__":
    pytest.main(["tests_integration"])
else:
    # When executed via `FreeCADCmd -c "import run_freecad_tests"`,
    # the module import will run this block.
    pytest.main(["tests_integration"])
