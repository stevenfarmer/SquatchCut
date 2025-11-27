import os
import sys


def _add_repo_core_to_path():
    """Ensure SquatchCut package under freecad/ is importable for tests."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    core_path = os.path.join(repo_root, "freecad")
    if core_path not in sys.path:
        sys.path.insert(0, core_path)


_add_repo_core_to_path()
