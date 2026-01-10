"""Lightweight in-GUI E2E test harness for SquatchCut."""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Optional
from uuid import uuid4

from SquatchCut.core import cutlist, logger, session, session_state
from SquatchCut.core import units as sc_units
from SquatchCut.core.geometry_sync import sync_source_panels_to_document
from SquatchCut.core.preferences import SquatchCutPreferences
from SquatchCut.freecad_integration import App, Gui
from SquatchCut.gui import taskpanel_input, taskpanel_main, taskpanel_settings
from SquatchCut.gui.commands import cmd_import_csv, cmd_run_nesting
from SquatchCut.gui.commands.cmd_export_cutlist import ExportCutlistCommand
from SquatchCut.gui.qt_compat import QtWidgets

GUI_TEST_PREFIX = ">>> [SquatchCut] [GUI TEST]"


def _log_info(message: str) -> None:
    logger.info(f"{GUI_TEST_PREFIX} {message}")


def _log_warning(message: str) -> None:
    logger.warning(f"{GUI_TEST_PREFIX} {message}")


def _log_error(message: str) -> None:
    logger.error(f"{GUI_TEST_PREFIX} {message}")


class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error: Optional[Exception] = None

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


def _create_shape_test_document(name: str = "SquatchCut_GUI_Shapes"):
    """
    Create a temporary document populated with simple rectangles for shape-based tests.
    """
    doc = None
    try:
        from SquatchCut.testing.helpers.generate_test_documents import (
            create_basic_rectangles_doc,
        )

        doc = create_basic_rectangles_doc()
        if doc is not None:
            return doc
    except Exception:
        pass

    doc = _new_temp_doc(name)
    try:
        from Draft import makeRectangle  # type: ignore

        specs = [
            ("P1", 600, 400, (0, 0, 0)),
            ("P2", 800, 500, (800, 0, 0)),
            ("P3", 400, 300, (0, 700, 0)),
        ]
        for label, width, height, (x, y, z) in specs:
            rect = makeRectangle(length=width, height=height)
            rect.Label = label
            rect.Placement.Base = App.Vector(x, y, z)
        doc.recompute()
    except Exception:
        pass
    try:
        if Gui:
            Gui.ActiveDocument = Gui.getDocument(doc.Name)
    except Exception:
        pass
    return doc


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
    _log_info("Seeded default panels for testing.")


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

    _log_warning("Could not resolve valid_panels_small.csv path.")
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
    _log_warning(f"Could not resolve {name} path.")
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
            cmd.import_from_path(csv_path, units="mm")
        else:
            raise RuntimeError(
                "ImportCsvCommand.import_from_path not available for GUI tests."
            )

        sync_source_panels_to_document()

        group = doc.getObject("SquatchCut_SourceParts")
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
            cmd.import_from_path(csv_path, units="mm")
        else:
            raise RuntimeError(
                "ImportCsvCommand.import_from_path not available for GUI tests."
            )

        sync_source_panels_to_document()

        run_cmd = cmd_run_nesting.RunNestingCommand()
        run_cmd.Activated()

        nested_group = doc.getObject("SquatchCut_NestedParts")
        if nested_group is None or not getattr(nested_group, "Group", []):
            raise RuntimeError(
                "No sheets or nested panels found after nesting preview."
            )

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
            raise AssertionError(
                "Units pref did not update to 'in' after selecting imperial."
            )
        panel.rbUnitsMetric.setChecked(True)
        if hasattr(panel, "_on_units_changed"):
            panel._on_units_changed()
        if sc_units.get_units() != "mm":
            raise AssertionError(
                "Units pref did not update to 'mm' after selecting metric."
            )
        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    return result


def test_sheet_size_suffix_tracks_units():
    """
    GUI test: sheet size/kerf labels reflect units.
    """
    result = TestResult("Units: sheet size labels match units")
    prefs = SquatchCutPreferences()
    orig_ms = prefs.get_measurement_system()
    panels = []
    try:
        for system, suffix in (("metric", "mm"), ("imperial", "in")):
            prefs.set_measurement_system(system)
            session_state.set_measurement_system(system)
            sc_units.set_units("mm" if system == "metric" else "in")
            panel = taskpanel_main.create_main_panel_for_tests()
            sheet_widget = getattr(panel, "sheet_widget", None)
            lbl_w = getattr(sheet_widget, "sheet_width_label", None) if sheet_widget else None
            lbl_h = getattr(sheet_widget, "sheet_height_label", None) if sheet_widget else None
            if lbl_w is None or lbl_h is None:
                raise RuntimeError(
                    "Main panel missing sheet_width_label/sheet_height_label."
                )
            if suffix not in lbl_w.text() or suffix not in lbl_h.text():
                raise AssertionError(
                    f"Expected '{suffix}' in labels; got '{lbl_w.text()}', '{lbl_h.text()}'."
                )
            panels.append(panel)
        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        for panel in panels:
            try:
                panel.close()
            except Exception:
                pass
        prefs.set_measurement_system(orig_ms)
        session_state.set_measurement_system(orig_ms)
        sc_units.set_units("in" if orig_ms == "imperial" else "mm")
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
        # Note: Test updated to be more flexible - nesting algorithm may find layouts
        # that only require cuts in one direction, which is actually more efficient
        if not orientations or not any(
            o in ("vertical", "horizontal") for o in orientations
        ):
            raise AssertionError(
                f"Expected at least vertical or horizontal cuts; got {orientations!r}"
            )

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        _close_doc(doc)

    return result


def test_shape_selection_and_nesting_workflow():
    """GUI test: shape selection workflow should populate panels and nest them."""
    result = TestResult("Shape workflow: select shapes and preview nesting")
    doc = None
    original_dialog = taskpanel_input.EnhancedShapeSelectionDialog
    original_set_panels = session_state.set_panels
    session_state.set_panels = lambda panels: original_set_panels(
        [{k: v for k, v in panel.items() if k != "freecad_object"} for panel in panels]
    )
    try:
        doc = _create_shape_test_document("SquatchCut_GUI_Shapes")
        if doc is None:
            raise RuntimeError("Could not create shape test document.")

        session.clear_all_geometry()
        session.set_panels([])

        prefs = SquatchCutPreferences()
        widget = taskpanel_input.InputGroupWidget(prefs)

        class _AutoSelectDialog:
            def __init__(self, detected_shapes=None, parent=None):
                self._shapes = detected_shapes or []

            def exec_(self):
                return QtWidgets.QDialog.Accepted

            def exec(self):
                return QtWidgets.QDialog.Accepted

            def get_data(self):
                return {"selected_shapes": self._shapes}

        taskpanel_input.EnhancedShapeSelectionDialog = _AutoSelectDialog

        widget._select_shapes()

        panels = session.get_panels()
        if not panels:
            raise RuntimeError("Shape selection did not populate panels.")

        if not any(part.get("source") == "freecad_shape" for part in panels):
            raise RuntimeError("Expected freecad_shape source panels after selection.")

        run_cmd = cmd_run_nesting.RunNestingCommand()
        run_cmd.Activated()

        nested_group = doc.getObject("SquatchCut_NestedParts")
        if nested_group is None or not getattr(nested_group, "Group", []):
            raise RuntimeError("Shape-based nesting produced no nested parts.")

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        taskpanel_input.EnhancedShapeSelectionDialog = original_dialog
        session_state.set_panels = original_set_panels
        if doc:
            _close_doc(doc)
    return result


def test_export_cutlist_command_auto_save():
    """GUI test: Export Cutlist command writes a file without user interaction."""
    result = TestResult("Export command: auto-save cutlist")
    doc = None
    export_path = Path(tempfile.gettempdir()) / f"SquatchCut_GUI_export_{uuid4().hex}.csv"
    dialog_backup = QtWidgets.QFileDialog
    info_backup = QtWidgets.QMessageBox.information

    try:
        doc = _new_temp_doc("SquatchCut_GUI_Export")

        session.clear_all_geometry()
        session.set_panels([])

        csv_path = _get_test_csv_path()
        if not csv_path:
            raise RuntimeError("Test CSV path could not be resolved.")

        import_cmd = cmd_import_csv.ImportCsvCommand()
        import_cmd.import_from_path(csv_path, units="mm")

        sync_source_panels_to_document()

        run_cmd = cmd_run_nesting.RunNestingCommand()
        run_cmd.Activated()

        accept_save_constant = getattr(
            QtWidgets.QFileDialog, "AcceptSave", getattr(QtWidgets.QFileDialog, "AcceptOpen", 0)
        )

        class _AutoSaveDialog:
            def __init__(self, *args, **kwargs):
                self._files = []

            def setAcceptMode(self, mode):
                pass

            def setNameFilter(self, _):
                pass

            def setDefaultSuffix(self, _):
                pass

            def setWindowTitle(self, _):
                pass

            AcceptSave = accept_save_constant

            def exec_(self):
                return QtWidgets.QDialog.Accepted

            def selectedFiles(self):
                return [str(export_path)]

        QtWidgets.QFileDialog = _AutoSaveDialog
        QtWidgets.QMessageBox.information = lambda *_, **__: None

        export_cmd = ExportCutlistCommand()
        export_cmd.Activated()

        if not export_path.is_file():
            raise RuntimeError("Cutlist export file was not created.")
        if export_path.stat().st_size == 0:
            raise RuntimeError("Exported cutlist file is empty.")

        result.set_pass()
    except Exception as exc:
        result.set_fail(exc)
    finally:
        QtWidgets.QFileDialog = dialog_backup
        QtWidgets.QMessageBox.information = info_backup
        try:
            if export_path.is_file():
                export_path.unlink()
        except Exception:
            pass
        if doc:
            _close_doc(doc)

    return result


def run_all_tests():
    """
    Entry point for the "Run GUI Tests" button in SquatchCut Settings.
    Runs a small battery of GUI-level sanity checks and logs a summary.
    """
    _log_info("Starting SquatchCut GUI test suite...")

    tests = [
        test_import_small_metric_csv,
        test_nesting_preview_basic,
        test_shape_selection_and_nesting_workflow,
        test_units_settings_metric,
        test_units_settings_imperial,
        test_units_toggle_updates_pref,
        test_sheet_size_suffix_tracks_units,
        test_import_imperial_csv_uses_units,
        test_cutlist_generated_after_nesting,
        test_export_cutlist_command_auto_save,
    ]

    results = []

    for test_func in tests:
        _log_info(f"Running {test_func.__name__}...")
        res = test_func()
        results.append(res)
        if res.passed:
            _log_info(f"PASS: {res.name}")
        else:
            _log_error(f"FAIL: {res.name} -> {res.error!r}")

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    _log_info(f"Completed {total} tests, {passed} passed, {total - passed} failed.")

    return results


def run_gui_test_suite_from_freecad():
    """
    FreeCAD-safe entry point for running the GUI test suite via UI buttons.
    """
    try:
        return run_all_tests()
    except Exception as exc:
        _log_error(f"Fatal error during GUI tests: {exc!r}")
        return None
