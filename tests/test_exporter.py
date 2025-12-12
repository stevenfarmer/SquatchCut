import csv
from pathlib import Path

from SquatchCut.core import exporter, session_state
from SquatchCut.core.exporter import ExportJob, ExportPartPlacement, ExportSheet
from SquatchCut.core.nesting import PlacedPart


def _sample_export_job(measurement_system="metric") -> ExportJob:
    return ExportJob(
        job_name="Test",
        measurement_system=measurement_system,
        sheets=[
            ExportSheet(
                sheet_index=0,
                width_mm=400,
                height_mm=300,
                parts=[
                    ExportPartPlacement("a", 0, 0, 0, 100, 50, 0),
                    ExportPartPlacement("b", 0, 10, 5, 80, 40, 90),
                ],
            ),
            ExportSheet(
                sheet_index=1,
                width_mm=600,
                height_mm=400,
                parts=[
                    ExportPartPlacement("c", 1, 20, 25, 60, 70, 0),
                ],
            ),
        ],
    )


def test_cutlist_csv_export_creates_file(tmp_path: Path):
    job = _sample_export_job("metric")
    out = tmp_path / "cutlist.csv"
    exporter.export_cutlist(job, str(out))
    assert out.exists()

    with out.open() as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        headers = reader.fieldnames
    assert headers == [
        "sheet_index",
        "sheet_width_mm",
        "sheet_height_mm",
        "part_id",
        "x_mm",
        "y_mm",
        "width_mm",
        "height_mm",
        "rotation_deg",
        "width_display",
        "height_display",
    ]
    assert rows[0]["sheet_index"] == "0"
    assert rows[1]["rotation_deg"] == "90"
    assert rows[0]["width_display"].endswith("mm")
    assert rows[0]["height_display"].endswith("mm")
    assert rows[-1]["sheet_index"] == "1"


def test_cutlist_csv_export_respects_imperial_units(tmp_path: Path):
    job = _sample_export_job("imperial")
    out = tmp_path / "cutlist_imperial.csv"
    exporter.export_cutlist(job, str(out))
    with out.open() as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert "in" in rows[0]["width_display"]
    assert "in" in rows[0]["height_display"]
    assert rows[1]["rotation_deg"] == "90"


def test_export_include_labels_dimensions_flags():
    job = _sample_export_job("metric")
    out_txt = Path.cwd() / "tmp_cutlist.txt"
    try:
        exporter.export_cutlist(job, str(out_txt), as_text=True)
    finally:
        if out_txt.exists():
            out_txt.unlink()


def _reset_session_state_for_export_tests():
    session_state.set_last_layout(None)
    session_state.clear_job_sheets()
    session_state.clear_sheet_size()
    session_state.set_sheet_mode("simple")
    session_state.set_measurement_system("metric")


def test_build_export_job_from_current_nesting_uses_session_layout():
    _reset_session_state_for_export_tests()
    session_state.set_measurement_system("imperial")
    session_state.set_sheet_mode("job_sheets")
    session_state.set_sheet_size(1200.0, 2400.0)
    session_state.set_job_sheets(
        [
            {"width_mm": 1000.0, "height_mm": 500.0, "quantity": 1},
            {"width_mm": 1500.0, "height_mm": 750.0, "quantity": 1},
        ]
    )
    placements = [
        PlacedPart(
            id="p1", sheet_index=0, x=0, y=0, width=100, height=50, rotation_deg=0
        ),
        PlacedPart(
            id="p2", sheet_index=1, x=10, y=15, width=80, height=40, rotation_deg=90
        ),
    ]
    session_state.set_last_layout(placements)

    job = exporter.build_export_job_from_current_nesting()

    assert job is not None
    assert job.measurement_system == "imperial"
    assert len(job.sheets) == 2
    assert job.sheets[0].parts[0].part_id == "p1"
    assert job.sheets[1].width_mm == 1500.0
    assert job.sheets[1].parts[0].rotation_deg == 90

    _reset_session_state_for_export_tests()


def test_build_export_job_returns_none_when_no_layout():
    _reset_session_state_for_export_tests()
    session_state.set_last_layout(None)
    assert exporter.build_export_job_from_current_nesting() is None


def test_cutlist_text_export_respects_imperial_units(tmp_path: Path):
    job = _sample_export_job("imperial")
    out = tmp_path / "cutlist_script.txt"
    exporter.export_cutlist(job, str(out), as_text=True)
    assert out.exists()
    content = out.read_text("utf-8")

    # Verify that content uses "in" and not "mm" for dimensions
    # Check that dimensions use inches, not millimeters
    import re

    # Look for dimension patterns like "X.X mm" but not "mm" in other contexts
    mm_dimensions = re.findall(r"\d+\.?\d*\s*mm\b", content)
    assert (
        len(mm_dimensions) == 0
    ), f"Text export should not contain metric dimensions when using Imperial, found: {mm_dimensions}"
    assert "in" in content, "Text export should contain 'in'"
