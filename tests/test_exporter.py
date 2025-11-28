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
