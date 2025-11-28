from pathlib import Path

from SquatchCut.core.cutlist import generate_cutlist
from SquatchCut.core.nesting import PlacedPart
from SquatchCut.core import exporter


def test_generate_cutlist_basic():
    placements = [
        PlacedPart(id="P1", sheet_index=0, x=0, y=0, width=100, height=100, rotation_deg=0),
        PlacedPart(id="P2", sheet_index=0, x=100, y=0, width=100, height=100, rotation_deg=0),
    ]
    cutlist = generate_cutlist(placements, (200, 100))
    assert 0 in cutlist
    cuts = cutlist[0]
    assert cuts, "Cuts should be generated"
    # Expect at least one vertical cut separating P1/P2
    rips = [c for c in cuts if c["cut_type"] == "RIP"]
    assert rips
    # Parts affected may be empty in simple layouts but should be present as list
    assert all("parts_affected" in c for c in cuts)


def test_export_cutlist_csv_and_text(tmp_path: Path):
    cutlist_map = {
        0: [
            {
                "sheet_index": 0,
                "cut_order": 1,
                "cut_type": "RIP",
                "cut_direction": "X",
                "from_edge": "LEFT",
                "distance_from_edge_mm": 100.0,
                "cut_length_mm": 200.0,
                "parts_affected": ["P1"],
                "notes": "",
            }
        ]
    }
    csv_path = tmp_path / "cutlist.csv"
    txt_path = tmp_path / "cutlist.txt"

    exporter.export_cutlist_map_to_csv(cutlist_map, csv_path)
    exporter.export_cutlist_to_text(cutlist_map, txt_path)

    assert csv_path.exists()
    assert txt_path.exists()
