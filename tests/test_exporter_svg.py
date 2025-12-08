from __future__ import annotations

from SquatchCut.core.exporter import export_layout_to_svg
from SquatchCut.core.nesting import PlacedPart


def _run_svg_export(tmp_path, **kwargs):
    base = tmp_path / "output.svg"
    files = export_layout_to_svg(
        kwargs["placements"],
        kwargs.get("sheet_size_mm", (400.0, 300.0)),
        doc=None,
        file_path=str(base),
        measurement_system=kwargs.get("measurement_system", "metric"),
        sheet_mode=kwargs.get("sheet_mode", "simple"),
        job_sheets=kwargs.get("job_sheets"),
        include_labels=kwargs.get("include_labels", True),
        include_dimensions=kwargs.get("include_dimensions", True),
    )
    return base, files


def test_export_svg_creates_one_file_per_sheet(tmp_path):
    placements = [
        PlacedPart(id="A", sheet_index=0, x=0, y=0, width=100, height=150, rotation_deg=0),
        PlacedPart(id="B", sheet_index=1, x=50, y=25, width=120, height=80, rotation_deg=90),
    ]
    _, files = _run_svg_export(tmp_path, placements=placements)

    assert len(files) == 2
    assert files[0].exists()
    assert files[1].exists()

    first_content = files[0].read_text()
    assert "Sheet 1 of 2" in first_content
    assert "A" in first_content
    assert "100 x 150 mm" in first_content

    second_content = files[1].read_text()
    assert "Sheet 2 of 2" in second_content
    assert "B" in second_content


def test_export_svg_respects_job_sheet_dimensions(tmp_path):
    placements = [
        PlacedPart(id="Only", sheet_index=1, x=10, y=10, width=50, height=75, rotation_deg=0),
    ]
    job_sheets = [
        {"width_mm": 500.0, "height_mm": 250.0, "quantity": 1},
        {"width_mm": 600.0, "height_mm": 200.0, "quantity": 1},
    ]
    _, files = _run_svg_export(
        tmp_path,
        placements=placements,
        job_sheets=job_sheets,
        sheet_mode="job_sheets",
    )

    assert len(files) == 1
    second_content = files[0].read_text()
    assert "Sheet 2 of 2 – 600 x 200 mm" in second_content


def test_export_svg_can_omit_labels(tmp_path):
    placements = [
        PlacedPart(id="Hidden", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0),
    ]
    _, files = _run_svg_export(
        tmp_path,
        placements=placements,
        include_labels=False,
    )

    content = files[0].read_text()
    assert "Hidden" not in content
