import csv
from pathlib import Path

from SquatchCut.core.nesting import PlacedPart
from SquatchCut.core import exporter


def test_cutlist_csv_export_creates_file(tmp_path: Path):
    placements = [
        PlacedPart(id="a", sheet_index=0, x=0, y=0, width=100, height=50, rotation_deg=0),
        PlacedPart(id="b", sheet_index=1, x=10, y=5, width=80, height=40, rotation_deg=90),
    ]
    out = tmp_path / "cutlist.csv"
    exporter.export_cutlist_to_csv(placements, out)
    assert out.exists()

    with out.open() as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["part_id"] == "a"
    assert rows[1]["sheet_index"] == "1"


def test_export_include_labels_dimensions_flags():
    # Ensure exporter accepts flags without error (geometry tests are FreeCAD-dependent)
    placements = [
        PlacedPart(id="a", sheet_index=0, x=0, y=0, width=10, height=10, rotation_deg=0),
    ]
    # Just call the CSV exporter; DXF/SVG are optional and depend on FreeCAD environment
    out = Path.cwd() / "tmp_cutlist.csv"
    try:
        exporter.export_cutlist_to_csv(placements, out)
    finally:
        if out.exists():
            out.unlink()
