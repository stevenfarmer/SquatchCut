"""Lightweight in-GUI E2E test harness for SquatchCut."""

from __future__ import annotations

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None

from SquatchCut.core import logger, session_state
from SquatchCut.core.geometry_sync import sync_source_panels_to_document
from SquatchCut.gui.commands import cmd_run_nesting
from SquatchCut.gui.qt_compat import QtWidgets


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error: Exception | None = None

    def set_pass(self):
        self.passed = True

    def set_fail(self, exc: Exception):
        self.passed = False
        self.error = exc


def _new_temp_doc(name: str = "SquatchCut_GUI_Test"):
    if App is None:
        raise RuntimeError("FreeCAD App module not available for GUI tests.")
    doc = App.newDocument(name)
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        try:
            Gui.ActiveDocument = Gui.ActiveDocument or None  # type: ignore
        except Exception:
            pass
    return doc


def _close_doc(doc):
    try:
        if App:
            App.closeDocument(doc.Name)
    except Exception:
        pass


def _ensure_default_panels():
    """Seed session with a tiny panel set if empty."""
    panels = session_state.get_panels()
    if panels:
        return
    default_panels = [
        {"id": "P1", "width": 300.0, "height": 200.0, "allow_rotate": False},
        {"id": "P2", "width": 150.0, "height": 150.0, "allow_rotate": True},
    ]
    session_state.set_panels(default_panels)
    logger.info("[GUI TEST] Seeded default panels for testing.")


def test_import_small_metric_csv():
    """
    E2E-ish: ensure panels are synced into a fresh document and geometry exists.
    """
    result = TestResult("Import small metric CSV")

    try:
        doc = _new_temp_doc()
    except Exception as exc:
        result.set_fail(exc)
        return result

    try:
        session_state.clear_panels()
        _ensure_default_panels()

        sync_source_panels_to_document()

        group = doc.getObject("SquatchCut_SourcePanels")
        if group is None or not getattr(group, "Group", []):
            raise RuntimeError("No source panel objects found after sync.")

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        _close_doc(doc)

    return result


def test_preview_nesting_small_metric():
    """
    E2E-ish: run nesting on the seeded panels and expect sheets/clones.
    """
    result = TestResult("Preview nesting small metric")

    try:
        doc = _new_temp_doc()
    except Exception as exc:
        result.set_fail(exc)
        return result

    try:
        session_state.clear_panels()
        _ensure_default_panels()

        sync_source_panels_to_document()

        run_cmd = cmd_run_nesting.RunNestingCommand()
        run_cmd.Activated()

        sheets_group = doc.getObject("SquatchCut_Sheets")
        if sheets_group is None or not getattr(sheets_group, "Group", []):
            raise RuntimeError("No sheets or nested panels found after nesting preview.")

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        _close_doc(doc)

    return result


def run_all_tests():
    """
    Entry point for the "Run GUI Tests" button in SquatchCut Settings.
    Runs a small battery of GUI-level sanity checks and logs a summary.
    """
    logger.info("[GUI TEST] Starting SquatchCut GUI test suite...")

    tests = [
        test_import_small_metric_csv,
        test_preview_nesting_small_metric,
    ]

    results = []

    for test_func in tests:
        logger.info(f"[GUI TEST] Running {test_func.__name__}...")
        res = test_func()
        results.append(res)
        if res.passed:
            logger.info(f"[GUI TEST] PASS: {res.name}")
        else:
            logger.error(f"[GUI TEST] FAIL: {res.name} -> {res.error!r}")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    logger.info(f"[GUI TEST] Completed {total} tests, {passed} passed, {total - passed} failed.")

    try:
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("SquatchCut GUI Tests")
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText(f"GUI tests completed.\n\nPassed: {passed}\nFailed: {total - passed}")
        msg.exec_()
    except Exception:
        pass

    return results
