"""Command to run lightweight SquatchCut GUI E2E tests."""

from __future__ import annotations

from SquatchCut.core import gui_tests, logger
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui.qt_compat import QtWidgets


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
            results = gui_tests.run_gui_test_suite_from_freecad()
            self._show_summary(results)
        except Exception as exc:
            logger.error(f"RunGuiTestsCommand failed: {exc!r}")

    def _show_summary(self, results):
        if Gui is None:
            return
        if results is None:
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("SquatchCut GUI Tests")
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("SquatchCut GUI tests failed to run. See Report view for details.")
            msg.exec_()
            return
        passed = sum(1 for result in results if result.passed)
        total = len(results)
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("SquatchCut GUI Tests")
        if passed == total:
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("SquatchCut GUI tests completed successfully. See report view for details.")
        else:
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("SquatchCut GUI tests completed with failures. See report view for details.")
        msg.setInformativeText(f"Passed: {passed}, Failed: {total - passed}")
        msg.exec_()


COMMAND = RunGuiTestsCommand()
