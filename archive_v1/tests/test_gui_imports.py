import importlib
import pkgutil

import pytest


def iter_squatchcut_gui_modules():
    """
    Dynamically discover all Python modules under SquatchCut.gui
    so that any new GUI files are automatically covered by this test.

    This assumes SquatchCut is installed in the pytest environment
    (i.e., tests are running from the repo root with SquatchCut importable).
    """
    import SquatchCut.gui as gui_pkg

    package_path = gui_pkg.__path__
    package_prefix = gui_pkg.__name__ + "."

    for module_info in pkgutil.walk_packages(package_path, package_prefix):
        # module_info.name is the full import path, e.g. "SquatchCut.gui.commands.cmd_run_nesting"
        yield module_info.name


@pytest.mark.parametrize("module_name", list(iter_squatchcut_gui_modules()))
def test_import_all_gui_modules(module_name):
    """
    Every GUI module (commands + taskpanels) must be importable
    in a non-FreeCAD environment.

    This catches:
      - Syntax errors
      - NameErrors at module import time
      - Missing imports
    """
    try:
        importlib.import_module(module_name)
    except Exception as e:
        pytest.fail(f"Failed to import GUI module '{module_name}': {e!r}")
