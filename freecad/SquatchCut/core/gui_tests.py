"""Lightweight in-GUI E2E test harness for SquatchCut."""

from __future__ import annotations

from pathlib import Path

try:
    import FreeCAD as App  # type: ignore
    import FreeCADGui as Gui  # type: ignore
except Exception:  # pragma: no cover
    App = None
    Gui = None

from SquatchCut.core import logger, session
from SquatchCut.core import cutlist
from SquatchCut.core.geometry_sync import sync_source_panels_to_document
from SquatchCut.gui.commands import cmd_run_nesting, cmd_import_csv
from SquatchCut.gui.qt_compat import QtWidgets
from SquatchCut.core import units as sc_units
from SquatchCut.gui import taskpanel_settings, taskpanel_main


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
    panels = session.get_panels()
    if panels:
        return
    default_panels = [
        {"id": "P1", "width": 300.0, "height": 200.0, "allow_rotate": False},
        {"id": "P2", "width": 150.0, "height": 150.0, "allow_rotate": True},
    ]
    session.set_panels(default_panels)
    logger.info("[GUI TEST] Seeded default panels for testing.")


def _get_test_csv_path():
    """
    Return the path to a known-good small metric CSV for tests.
    """
    try:
        import SquatchCut

        mod_path = Path(SquatchCut.__file__).resolve().parent
        csv_path = mod_path.parent / "testing" / "csv" / "valid_panels_small.csv"
        if csv_path.is_file():
            return str(csv_path)
    except Exception:
        pass

    logger.warning("GUI tests: could not resolve valid_panels_small.csv path.")
    return None


def _get_imperial_test_csv_path(name: str = "valid_panels_imperial_1_sheet.csv"):
    """
    Return the path to an imperial CSV for tests.
    """
    try:
        import SquatchCut

        mod_path = Path(SquatchCut.__file__).resolve().parent
        csv_path = mod_path / "freecad" / "testing" / "csv" / name
        if csv_path.is_file():
            return str(csv_path)
        # Fallback to legacy location if needed
        fallback = mod_path.parent / "testing" / "csv" / name
        if fallback.is_file():
            return str(fallback)
    except Exception:
        pass
    logger.warning(f"GUI tests: could not resolve {name} path.")
    return None


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
        session.clear_all_geometry()
        session.set_panels([])

        csv_path = _get_test_csv_path()
        if not csv_path:
            raise RuntimeError("Test CSV path could not be resolved.")

        cmd = cmd_import_csv.ImportCsvCommand()
        if hasattr(cmd, "import_from_path"):
            cmd.import_from_path(csv_path)
        else:
            raise RuntimeError("ImportCsvCommand.import_from_path not available for GUI tests.")

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


def test_nesting_preview_basic():
    """
    GUI test: import CSV, sync panels, run nesting, verify sheets exist.
    """
    result = TestResult("Preview nesting basic")

    try:
        doc = _new_temp_doc()
    except Exception as exc:
        result.set_fail(exc)
        return result

    try:
        session.clear_all_geometry()
        session.set_panels([])

        csv_path = _get_test_csv_path()
        if not csv_path:
            raise RuntimeError("Test CSV path could not be resolved.")

        cmd = cmd_import_csv.ImportCsvCommand()
        if hasattr(cmd, "import_from_path"):
            cmd.import_from_path(csv_path)
        else:
            raise RuntimeError("ImportCsvCommand.import_from_path not available for GUI tests.")

        sync_source_panels_to_document()

        run_cmd = cmd_run_nesting.RunNestingCommand()
        run_cmd.Activated()

        sheets_group = doc.getObject("SquatchCut_Sheets")
        if sheets_group is None or not getattr(sheets_group, "Group", []):
            raise RuntimeError("No sheets or nested panels found after nesting preview.")

        if not session.get_source_panel_objects():
            raise RuntimeError("Session lost source panel objects after nesting.")

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        _close_doc(doc)

    return result


def test_units_settings_metric():
    """
    GUI test: when units pref is 'mm', settings panel shows Metric selected.
    """
    result = TestResult("Units: Settings reflects Metric (mm)")

    try:
        sc_units.set_units("mm")
        panel = taskpanel_settings.create_settings_panel_for_tests()

        metric = getattr(panel, "rbUnitsMetric", None)
        imperial = getattr(panel, "rbUnitsImperial", None)
        if metric is None or imperial is None:
            raise RuntimeError("Settings panel missing unit radio buttons.")
        if not metric.isChecked():
            raise AssertionError("Metric radio not checked for units='mm'.")
        if imperial.isChecked():
            raise AssertionError("Imperial radio incorrectly checked for units='mm'.")
        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    return result


def test_units_settings_imperial():
    """
    GUI test: when units pref is 'in', settings panel shows Imperial selected.
    """
    result = TestResult("Units: Settings reflects Imperial (in)")

    try:
        sc_units.set_units("in")
        panel = taskpanel_settings.create_settings_panel_for_tests()

        metric = getattr(panel, "rbUnitsMetric", None)
        imperial = getattr(panel, "rbUnitsImperial", None)
        if metric is None or imperial is None:
            raise RuntimeError("Settings panel missing unit radio buttons.")
        if not imperial.isChecked():
            raise AssertionError("Imperial radio not checked for units='in'.")
        if metric.isChecked():
            raise AssertionError("Metric radio incorrectly checked for units='in'.")
        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    return result


def test_units_toggle_updates_pref():
    """
    GUI test: toggling radios updates the units preference.
    """
    result = TestResult("Units: toggling radios updates preference")
    try:
        sc_units.set_units("mm")
        panel = taskpanel_settings.create_settings_panel_for_tests()
        panel.rbUnitsImperial.setChecked(True)
        if hasattr(panel, "_on_units_changed"):
            panel._on_units_changed()
        if sc_units.get_units() != "in":
            raise AssertionError("Units pref did not update to 'in' after selecting imperial.")
        panel.rbUnitsMetric.setChecked(True)
        if hasattr(panel, "_on_units_changed"):
            panel._on_units_changed()
        if sc_units.get_units() != "mm":
            raise AssertionError("Units pref did not update to 'mm' after selecting metric.")
        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    return result


def test_sheet_size_suffix_tracks_units():
    """
    GUI test: sheet size spinbox suffix reflects units.
    """
    result = TestResult("Units: sheet size suffix matches units")
    try:
        sc_units.set_units("mm")
        panel_mm = taskpanel_main.create_main_panel_for_tests()
        sb_w = getattr(panel_mm, "sheet_width_spin", None)
        sb_h = getattr(panel_mm, "sheet_height_spin", None)
        if sb_w is None or sb_h is None:
            raise RuntimeError("Main panel missing sheet_width_spin/sheet_height_spin.")
        suffix_w = sb_w.suffix().strip()
        suffix_h = sb_h.suffix().strip()
        if "mm" not in suffix_w or "mm" not in suffix_h:
            raise AssertionError(f"Expected 'mm' in suffix; got '{suffix_w}', '{suffix_h}'.")

        sc_units.set_units("in")
        panel_in = taskpanel_main.create_main_panel_for_tests()
        sb_w_in = getattr(panel_in, "sheet_width_spin", None)
        sb_h_in = getattr(panel_in, "sheet_height_spin", None)
        suffix_w_in = sb_w_in.suffix().strip()
        suffix_h_in = sb_h_in.suffix().strip()
        if "in" not in suffix_w_in or "in" not in suffix_h_in:
            raise AssertionError(f"Expected 'in' in suffix; got '{suffix_w_in}', '{suffix_h_in}'.")

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    return result


def test_import_imperial_csv_uses_units():
    """
    GUI test: import imperial CSV with units='in' and ensure panels are created.
    """
    result = TestResult("Import imperial CSV respects units")

    try:
        doc = _new_temp_doc("SquatchCut_GUI_Imperial")
    except Exception as exc:
        result.set_fail(exc)
        return result

    try:
        session.clear_all_geometry()
        session.set_panels([])

        csv_path = _get_imperial_test_csv_path()
        if not csv_path:
            raise RuntimeError("Imperial test CSV path could not be resolved.")

        cmd = cmd_import_csv.ImportCsvCommand()
        cmd.import_from_path(csv_path, units="in")

        sync_source_panels_to_document()

        source_objs = session.get_source_panel_objects()
        if not source_objs:
            raise RuntimeError("No source panel objects after imperial CSV import.")

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        _close_doc(doc)

    return result


def test_cutlist_generated_after_nesting():
    """
    GUI test: after nesting, cutlist generator should return cuts.
    """
    result = TestResult("Cutlist: generated after nesting")

    try:
        doc = _new_temp_doc("SquatchCut_GUI_Cutlist")
    except Exception as exc:
        result.set_fail(exc)
        return result

    try:
        session.clear_all_geometry()
        session.set_panels([])

        csv_path = _get_test_csv_path()
        if not csv_path:
            raise RuntimeError("Metric test CSV path could not be resolved.")

        from SquatchCut.gui.commands import cmd_import_csv, cmd_run_nesting

        cmd_i = cmd_import_csv.ImportCsvCommand()
        cmd_i.import_from_path(csv_path, units="mm")

        from SquatchCut.core.geometry_sync import sync_source_panels_to_document
        sync_source_panels_to_document()

        run_cmd = cmd_run_nesting.RunNestingCommand()
        run_cmd.Activated()

        cuts = cutlist.generate_cutops_from_session()
        if not cuts:
            raise RuntimeError("Cutlist generator returned no cuts.")
        orientations = {c.orientation for c in cuts}
        if "vertical" not in orientations or "horizontal" not in orientations:
            raise AssertionError(f"Expected both vertical and horizontal cuts; got {orientations!r}")

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
        test_nesting_preview_basic,
        test_units_settings_metric,
        test_units_settings_imperial,
        test_units_toggle_updates_pref,
        test_sheet_size_suffix_tracks_units,
        test_import_imperial_csv_uses_units,
        test_cutlist_generated_after_nesting,
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
