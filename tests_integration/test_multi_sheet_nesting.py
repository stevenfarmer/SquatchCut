"""Integration tests covering multi-sheet nesting workflows."""

from pathlib import Path

import pytest

pytest.importorskip("FreeCAD")
pytest.importorskip("FreeCADGui")

import FreeCAD  # type: ignore
from SquatchCut import settings
from SquatchCut.core import session, session_state
from SquatchCut.core.cutlist import generate_cutops_from_session
from SquatchCut.gui.commands.cmd_import_csv import run_csv_import
from SquatchCut.gui.commands.cmd_run_nesting import RunNestingCommand


def _csv_path(name: str) -> str:
    base = Path(__file__).resolve().parent.parent
    return str(base / "freecad" / "testing" / "csv" / name)


def _new_doc(name: str):
    try:
        FreeCAD.closeDocument(name)
    except Exception:
        pass
    return FreeCAD.newDocument(name)


def _reset_session_state():
    session_state.clear_job_sheets()
    session_state.clear_panels()
    session_state.clear_sheet_size()
    session_state.set_measurement_system("metric")
    session_state.set_sheet_mode("simple")
    settings.hydrate_from_params()


def test_multi_sheet_nesting_creates_and_cleans_boundaries():
    _reset_session_state()
    doc = _new_doc("MultiSheetTest")
    try:
        run_csv_import(doc, _csv_path("valid_panels_multi_sheet.csv"), csv_units="metric")
        session_state.set_job_sheets(
            [
                {"width_mm": 600.0, "height_mm": 1200.0, "quantity": 1, "label": "Sheet A"},
                {"width_mm": 600.0, "height_mm": 1200.0, "quantity": 1, "label": "Sheet B"},
            ]
        )
        session_state.set_sheet_mode("job_sheets")
        session_state.set_sheet_size(600.0, 1200.0)

        cmd = RunNestingCommand()
        cmd.Activated()

        boundaries = [obj for obj in getattr(doc, "Objects", []) or [] if obj.Name.startswith("SquatchCut_Sheet")]
        assert len(boundaries) == 2, "Expected one boundary per configured sheet"
        assert len(session.get_sheet_objects()) == 2
        nested_objs = session.get_nested_panel_objects()
        assert nested_objs
        initial_nested_count = len(nested_objs)
        assert any(getattr(obj.Placement, "Base", FreeCAD.Vector(0, 0, 0)).x > 600.0 for obj in nested_objs)
        assert session.get_source_panel_objects(), "Source panel objects should persist after nesting"

        cut_ops = generate_cutops_from_session()
        sheet_indices = {op.sheet_index for op in cut_ops}
        assert 1 in sheet_indices and 2 in sheet_indices

        cmd2 = RunNestingCommand()
        cmd2.Activated()

        boundaries_after = [obj for obj in getattr(doc, "Objects", []) or [] if obj.Name.startswith("SquatchCut_Sheet")]
        assert len(boundaries_after) == 2
        assert len(session.get_nested_panel_objects()) == initial_nested_count
        assert session.get_source_panel_objects(), "Source panels should remain tracked after repeated runs"
    finally:
        try:
            FreeCAD.closeDocument(doc.Name)
        except Exception:
            pass
        _reset_session_state()


def test_simple_mode_repeats_default_sheet_size():
    _reset_session_state()
    doc = _new_doc("SimpleSheetMode")
    try:
        run_csv_import(doc, _csv_path("valid_panels_multi_sheet.csv"), csv_units="metric")
        session_state.set_sheet_size(600.0, 1200.0)
        session_state.set_sheet_mode("simple")

        cmd = RunNestingCommand()
        cmd.Activated()

        sheet_objects = session.get_sheet_objects()
        assert len(sheet_objects) >= 2, "Expected multiple sheet boundaries in simple mode."
        assert session_state.get_sheet_mode() == "simple"
    finally:
        try:
            FreeCAD.closeDocument(doc.Name)
        except Exception:
            pass
        _reset_session_state()
