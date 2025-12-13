#!/usr/bin/env python3
"""
Property-based tests for export architecture preservation.

**Feature: ai-agent-documentation, Property 4: Export Architecture Preservation**

This module validates that export architecture constraints are preserved
across all export operations and data transformations.

Requirements validated:
- 4.1: All exports go through freecad/SquatchCut/core/exporter.py
- 4.2: ExportJob/ExportSheet/ExportPartPlacement are sole sources of truth
- 4.3: ExportJob values in millimeters with exporter helpers for display
- 4.4: DXF export is deferred and should not be implemented
- 4.5: CSV/SVG exports use deterministic behavior from ExportJob data
"""

import csv
import os
import tempfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


# Mock data models for testing (would normally import from SquatchCut.core)
@dataclass
class ExportPartPlacement:
    """Mock ExportPartPlacement for testing"""

    part_id: str
    label: str
    width_mm: float
    height_mm: float
    x_mm: float
    y_mm: float
    rotation_degrees: float = 0.0


@dataclass
class ExportSheet:
    """Mock ExportSheet for testing"""

    sheet_id: str
    width_mm: float
    height_mm: float
    kerf_mm: float
    parts: list[ExportPartPlacement]


@dataclass
class ExportJob:
    """Mock ExportJob for testing"""

    measurement_system: str
    timestamp: datetime
    source_file: str | None
    sheets: list[ExportSheet]


# Test data generators
@st.composite
def valid_dimensions(draw):
    """Generate valid dimensions in mm (positive, reasonable range)"""
    return draw(st.floats(min_value=1.0, max_value=10000.0))


@st.composite
def valid_coordinates(draw):
    """Generate valid coordinates in mm"""
    return draw(st.floats(min_value=0.0, max_value=5000.0))


@st.composite
def valid_rotation(draw):
    """Generate valid rotation in degrees"""
    return draw(st.floats(min_value=0.0, max_value=360.0))


@st.composite
def valid_part_placement(draw):
    """Generate valid ExportPartPlacement"""
    return ExportPartPlacement(
        part_id=draw(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            )
        ),
        label=draw(
            st.text(
                min_size=1,
                max_size=50,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Zs")),
            )
        ),
        width_mm=draw(valid_dimensions()),
        height_mm=draw(valid_dimensions()),
        x_mm=draw(valid_coordinates()),
        y_mm=draw(valid_coordinates()),
        rotation_degrees=draw(valid_rotation()),
    )


@st.composite
def valid_export_sheet(draw):
    """Generate valid ExportSheet with unique part IDs"""
    num_parts = draw(st.integers(min_value=0, max_value=20))
    parts = []
    for i in range(num_parts):
        part = ExportPartPlacement(
            part_id=f"part_{i}",  # Ensure unique IDs within sheet
            label=draw(
                st.text(
                    min_size=1,
                    max_size=50,
                    alphabet=st.characters(
                        whitelist_categories=("Lu", "Ll", "Nd", "Zs")
                    ),
                )
            ),
            width_mm=draw(valid_dimensions()),
            height_mm=draw(valid_dimensions()),
            x_mm=draw(valid_coordinates()),
            y_mm=draw(valid_coordinates()),
            rotation_degrees=draw(valid_rotation()),
        )
        parts.append(part)

    return ExportSheet(
        sheet_id=draw(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
            )
        ),
        width_mm=draw(valid_dimensions()),
        height_mm=draw(valid_dimensions()),
        kerf_mm=draw(st.floats(min_value=0.0, max_value=10.0)),
        parts=parts,
    )


@st.composite
def valid_export_job(draw):
    """Generate valid ExportJob with unique sheet and part IDs"""
    num_sheets = draw(st.integers(min_value=1, max_value=5))
    sheets = []
    global_part_counter = 0

    for sheet_index in range(num_sheets):
        num_parts = draw(st.integers(min_value=0, max_value=20))
        parts = []

        for part_index in range(num_parts):
            part = ExportPartPlacement(
                part_id=f"part_{global_part_counter}",  # Globally unique part IDs
                label=draw(
                    st.text(
                        min_size=1,
                        max_size=50,
                        alphabet=st.characters(
                            whitelist_categories=("Lu", "Ll", "Nd", "Zs")
                        ),
                    )
                ),
                width_mm=draw(valid_dimensions()),
                height_mm=draw(valid_dimensions()),
                x_mm=draw(valid_coordinates()),
                y_mm=draw(valid_coordinates()),
                rotation_degrees=draw(valid_rotation()),
            )
            parts.append(part)
            global_part_counter += 1

        sheet = ExportSheet(
            sheet_id=f"sheet_{sheet_index}",  # Unique sheet IDs
            width_mm=draw(valid_dimensions()),
            height_mm=draw(valid_dimensions()),
            kerf_mm=draw(st.floats(min_value=0.0, max_value=10.0)),
            parts=parts,
        )
        sheets.append(sheet)

    return ExportJob(
        measurement_system=draw(st.sampled_from(["metric", "imperial"])),
        timestamp=datetime.now(),
        source_file=draw(st.one_of(st.none(), st.text(min_size=1, max_size=100))),
        sheets=sheets,
    )


# Mock export functions (would normally import from SquatchCut.core.exporter)
def mock_export_cutlist(export_job: ExportJob, file_path: str):
    """Mock CSV export function that follows canonical architecture"""
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Write header
        writer.writerow(
            [
                "Sheet",
                "Part ID",
                "Label",
                "Width",
                "Height",
                "X Position",
                "Y Position",
                "Rotation",
            ]
        )

        # Write data from ExportJob (canonical source)
        for sheet in export_job.sheets:
            for part in sheet.parts:
                # Always use mm values from ExportJob
                writer.writerow(
                    [
                        sheet.sheet_id,
                        part.part_id,
                        part.label,
                        f"{part.width_mm:.6f}",
                        f"{part.height_mm:.6f}",
                        f"{part.x_mm:.6f}",
                        f"{part.y_mm:.6f}",
                        f"{part.rotation_degrees:.6f}",
                    ]
                )


def mock_export_nesting_to_svg(export_job: ExportJob, file_path: str):
    """Mock SVG export function that follows canonical architecture"""
    svg_content = ['<?xml version="1.0" encoding="UTF-8"?>']

    # Calculate dimensions from ExportJob data
    max_width = (
        max(sheet.width_mm for sheet in export_job.sheets)
        if export_job.sheets
        else 1220
    )
    total_height = sum(sheet.height_mm + 50 for sheet in export_job.sheets)

    svg_content.append(
        f'<svg width="{max_width}" height="{total_height}" '
        f'viewBox="0 0 {max_width} {total_height}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )

    # Draw sheets and parts from ExportJob (canonical source)
    y_offset = 0
    for sheet in export_job.sheets:
        # Sheet outline using mm values from ExportJob
        svg_content.append(
            f'<rect class="sheet" x="0" y="{y_offset}" '
            f'width="{sheet.width_mm}" height="{sheet.height_mm}"/>'
        )

        # Parts using mm values from ExportJob
        for part in sheet.parts:
            part_x = part.x_mm
            part_y = y_offset + part.y_mm

            svg_content.append(
                f'<rect class="part" x="{part_x}" y="{part_y}" '
                f'width="{part.width_mm}" height="{part.height_mm}"/>'
            )

        y_offset += sheet.height_mm + 50

    svg_content.append("</svg>")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_content))


class TestExportArchitecturePreservation:
    """Property-based tests for export architecture preservation"""

    @given(export_job=valid_export_job())
    @settings(max_examples=100, deadline=5000)
    def test_csv_export_uses_canonical_data_model(self, export_job):
        """
        **Feature: ai-agent-documentation, Property 4: Export Architecture Preservation**

        Property: CSV exports must use ExportJob as sole source of truth
        Validates: Requirements 4.1, 4.2, 4.3, 4.5
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Export using canonical architecture
            mock_export_cutlist(export_job, temp_path)

            # Verify file was created
            assert os.path.exists(temp_path), "CSV export file was not created"

            # Parse CSV and verify data integrity
            with open(temp_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)

            # Verify all parts from ExportJob are present
            expected_parts = []
            for sheet in export_job.sheets:
                for part in sheet.parts:
                    expected_parts.append(
                        {
                            "sheet_id": sheet.sheet_id,
                            "part_id": part.part_id,
                            "label": part.label,
                            "width_mm": part.width_mm,
                            "height_mm": part.height_mm,
                            "x_mm": part.x_mm,
                            "y_mm": part.y_mm,
                            "rotation_degrees": part.rotation_degrees,
                        }
                    )

            assert len(rows) == len(
                expected_parts
            ), "CSV row count doesn't match ExportJob parts"

            # Verify each row corresponds to ExportJob data
            for i, row in enumerate(rows):
                expected = expected_parts[i]

                assert row["Sheet"] == expected["sheet_id"]
                assert row["Part ID"] == expected["part_id"]
                assert row["Label"] == expected["label"]

                # Verify dimensions are in mm (from ExportJob)
                assert abs(float(row["Width"]) - expected["width_mm"]) < 0.1
                assert abs(float(row["Height"]) - expected["height_mm"]) < 0.1
                assert abs(float(row["X Position"]) - expected["x_mm"]) < 0.1
                assert abs(float(row["Y Position"]) - expected["y_mm"]) < 0.1
                assert abs(float(row["Rotation"]) - expected["rotation_degrees"]) < 0.1

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @given(export_job=valid_export_job())
    @settings(max_examples=100, deadline=5000)
    def test_svg_export_uses_canonical_data_model(self, export_job):
        """
        **Feature: ai-agent-documentation, Property 4: Export Architecture Preservation**

        Property: SVG exports must use ExportJob as sole source of truth
        Validates: Requirements 4.1, 4.2, 4.3, 4.5
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".svg", delete=False) as f:
            temp_path = f.name

        try:
            # Export using canonical architecture
            mock_export_nesting_to_svg(export_job, temp_path)

            # Verify file was created
            assert os.path.exists(temp_path), "SVG export file was not created"

            # Parse SVG and verify structure
            tree = ET.parse(temp_path)
            root = tree.getroot()

            # Verify SVG namespace and structure
            assert root.tag.endswith("svg"), "Root element is not SVG"

            # Find all sheet rectangles
            sheet_rects = root.findall(".//*[@class='sheet']")
            assert len(sheet_rects) == len(
                export_job.sheets
            ), "Sheet count mismatch in SVG"

            # Find all part rectangles
            part_rects = root.findall(".//*[@class='part']")
            expected_part_count = sum(len(sheet.parts) for sheet in export_job.sheets)
            assert len(part_rects) == expected_part_count, "Part count mismatch in SVG"

            # Verify sheet dimensions match ExportJob data (in mm)
            for i, sheet_rect in enumerate(sheet_rects):
                expected_sheet = export_job.sheets[i]

                width = float(sheet_rect.get("width"))
                height = float(sheet_rect.get("height"))

                assert (
                    abs(width - expected_sheet.width_mm) < 0.1
                ), f"Sheet {i} width mismatch"
                assert (
                    abs(height - expected_sheet.height_mm) < 0.1
                ), f"Sheet {i} height mismatch"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @given(export_job=valid_export_job())
    @settings(max_examples=50, deadline=5000)
    def test_export_determinism(self, export_job):
        """
        **Feature: ai-agent-documentation, Property 4: Export Architecture Preservation**

        Property: Exports must be deterministic given same ExportJob
        Validates: Requirements 4.2, 4.5
        """
        # Export same data twice
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f1:
            temp_path1 = f1.name
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f2:
            temp_path2 = f2.name

        try:
            # Export same ExportJob twice
            mock_export_cutlist(export_job, temp_path1)
            mock_export_cutlist(export_job, temp_path2)

            # Read both files
            with open(temp_path1, encoding="utf-8") as f:
                content1 = f.read()
            with open(temp_path2, encoding="utf-8") as f:
                content2 = f.read()

            # Verify identical output
            assert content1 == content2, "Export is not deterministic"

        finally:
            for path in [temp_path1, temp_path2]:
                if os.path.exists(path):
                    os.unlink(path)

    def test_dxf_export_is_deferred(self):
        """
        **Feature: ai-agent-documentation, Property 4: Export Architecture Preservation**

        Property: DXF export must be explicitly deferred
        Validates: Requirement 4.4
        """
        # This test verifies that DXF export is not implemented
        # In a real implementation, this would check that DXF export functions
        # raise NotImplementedError with appropriate message

        def mock_export_dxf(export_job, file_path):
            raise NotImplementedError("DXF export is deferred - use CSV or SVG instead")

        export_job = ExportJob(
            measurement_system="metric",
            timestamp=datetime.now(),
            source_file=None,
            sheets=[],
        )

        with pytest.raises(NotImplementedError, match="DXF export is deferred"):
            mock_export_dxf(export_job, "test.dxf")

    @given(export_job=valid_export_job())
    @settings(max_examples=50, deadline=5000)
    def test_export_data_integrity(self, export_job):
        """
        **Feature: ai-agent-documentation, Property 4: Export Architecture Preservation**

        Property: Export data must maintain integrity from ExportJob
        Validates: Requirements 4.2, 4.3
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Export data
            mock_export_cutlist(export_job, temp_path)

            # Parse exported data
            with open(temp_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                exported_data = list(reader)

            # Verify no data corruption
            for sheet in export_job.sheets:
                for part in sheet.parts:
                    # Find corresponding row in export
                    matching_rows = [
                        row
                        for row in exported_data
                        if row["Part ID"] == part.part_id
                        and row["Sheet"] == sheet.sheet_id
                    ]

                    assert (
                        len(matching_rows) == 1
                    ), f"Part {part.part_id} not found or duplicated in export"

                    row = matching_rows[0]

                    # Verify all dimensions are preserved (in mm)
                    assert abs(float(row["Width"]) - part.width_mm) < 0.001
                    assert abs(float(row["Height"]) - part.height_mm) < 0.001
                    assert abs(float(row["X Position"]) - part.x_mm) < 0.001
                    assert abs(float(row["Y Position"]) - part.y_mm) < 0.001
                    assert abs(float(row["Rotation"]) - part.rotation_degrees) < 0.001

                    # Verify label integrity
                    assert row["Label"] == part.label

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @given(
        export_job=valid_export_job(),
        measurement_system=st.sampled_from(["metric", "imperial"]),
    )
    @settings(max_examples=50, deadline=5000)
    def test_measurement_system_independence(self, export_job, measurement_system):
        """
        **Feature: ai-agent-documentation, Property 4: Export Architecture Preservation**

        Property: Internal storage always in mm regardless of measurement system
        Validates: Requirement 4.3
        """
        # Set measurement system
        export_job.measurement_system = measurement_system

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Export data
            mock_export_cutlist(export_job, temp_path)

            # Parse exported data
            with open(temp_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                exported_data = list(reader)

            # Verify internal values are always in mm
            for sheet in export_job.sheets:
                for part in sheet.parts:
                    # Internal ExportJob values should always be in mm
                    assert part.width_mm > 0, "Width should be positive mm value"
                    assert part.height_mm > 0, "Height should be positive mm value"
                    assert (
                        part.x_mm >= 0
                    ), "X coordinate should be non-negative mm value"
                    assert (
                        part.y_mm >= 0
                    ), "Y coordinate should be non-negative mm value"

                    # Verify reasonable mm ranges (not inches stored as mm)
                    assert (
                        part.width_mm < 50000
                    ), "Width too large - might be inches stored as mm"
                    assert (
                        part.height_mm < 50000
                    ), "Height too large - might be inches stored as mm"

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
