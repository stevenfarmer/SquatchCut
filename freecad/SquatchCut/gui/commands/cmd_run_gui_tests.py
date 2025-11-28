"""Command to run lightweight SquatchCut GUI E2E tests."""

from __future__ import annotations

try:
    import FreeCAD as App
    import FreeCADGui as Gui
except Exception:
    App = None
    Gui = None

from SquatchCut.core import gui_tests, logger


class RunGuiTestsCommand:
    """Run the SquatchCut GUI test harness."""

    def GetResources(self):
        return {
            "MenuText": "Run GUI Tests",
            "ToolTip": "Run SquatchCut GUI end-to-end sanity tests",
            "Pixmap": "",
        }

    def IsActive(self):
        return App is not None and Gui is not None

    def Activated(self):
        if App is None or Gui is None:
            return
        try:
            gui_tests.run_all_tests()
        except Exception as exc:
            logger.error(f"RunGuiTestsCommand failed: {exc!r}")


COMMAND = RunGuiTestsCommand()
