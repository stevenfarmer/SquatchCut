from __future__ import annotations

import xml.etree.ElementTree as ET

from SquatchCut.core.exporter import (
    ExportJob,
    ExportPartPlacement,
    ExportSheet,
    export_nesting_to_svg,
)


def _make_job(sheet_defs, measurement_system="metric"):
    sheets = []
    for idx, entry in enumerate(sheet_defs):
        sheets.append(
            ExportSheet(
                sheet_index=idx,
                width_mm=entry["width"],
                height_mm=entry["height"],
                parts=entry["parts"],
            )
        )
    return ExportJob(job_name="Test", measurement_system=measurement_system, sheets=sheets)


def _run_svg_export(tmp_path, job, **kwargs):
    base = tmp_path / "output.svg"
    files = export_nesting_to_svg(
        job,
        str(base),
        include_labels=kwargs.get("include_labels", True),
        include_dimensions=kwargs.get("include_dimensions", True),
    )
    return base, files


def test_export_svg_creates_one_file_per_sheet(tmp_path):
    job = _make_job(
        [
            {
                "width": 400,
                "height": 300,
                "parts": [
                    ExportPartPlacement("A", 0, 0, 0, 100, 150, 0),
                ],
            },
            {
                "width": 400,
                "height": 300,
                "parts": [
                    ExportPartPlacement("B", 1, 50, 25, 120, 80, 90),
                ],
            },
        ]
    )
    _, files = _run_svg_export(tmp_path, job)

    assert len(files) == 2
    for path in files:
        assert path.exists()

    first_tree = ET.parse(files[0])
    first_root = first_tree.getroot()
    rects = first_root.findall(".//{http://www.w3.org/2000/svg}rect")
    assert any("sheet-border" in (rect.get("class") or "") for rect in rects)
    part_rects = [r for r in rects if "part-rect" in (r.get("class") or "")]
    assert len(part_rects) == 1
    assert part_rects[0].get("width") == "100"

    texts = ["".join(elem.itertext()) for elem in first_root.findall(".//{http://www.w3.org/2000/svg}text")]
    assert any("Sheet 1 of 2" in text for text in texts)
    assert any("A" in text for text in texts)


def test_export_svg_respects_job_sheet_dimensions(tmp_path):
    job = _make_job(
        [
            {
                "width": 500,
                "height": 250,
                "parts": [],
            },
            {
                "width": 600,
                "height": 200,
                "parts": [
                    ExportPartPlacement("Only", 1, 10, 10, 50, 75, 0),
                ],
            },
        ]
    )
    _, files = _run_svg_export(tmp_path, job)

    assert len(files) == 2
    second_texts = ["".join(elem.itertext()) for elem in ET.parse(files[1]).getroot().findall(".//{http://www.w3.org/2000/svg}text")]
    assert any("Sheet 2 of 2 – 600 x 200 mm" in text for text in second_texts)


def test_export_svg_can_omit_labels(tmp_path):
    job = _make_job(
        [
            {
                "width": 400,
                "height": 300,
                "parts": [ExportPartPlacement("Hidden", 0, 0, 0, 100, 100, 0)],
            }
        ]
    )
    _, files = _run_svg_export(tmp_path, job, include_labels=False)

    content = files[0].read_text()
    assert "Hidden" not in content


def test_export_svg_imperial_labels(tmp_path):
    job = _make_job(
        [
            {
                "width": 500,
                "height": 250,
                "parts": [ExportPartPlacement("Imp", 0, 0, 0, 63.5, 63.5, 0)],
            }
        ],
        measurement_system="imperial",
    )
    _, files = _run_svg_export(tmp_path, job)
    text_nodes = ET.parse(files[0]).getroot().findall(".//{http://www.w3.org/2000/svg}text")
    text_content = " ".join("".join(node.itertext()) for node in text_nodes)
    assert "in" in text_content
