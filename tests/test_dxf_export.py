"""Tests for DXF export functionality."""

from unittest.mock import MagicMock, patch

import pytest
from SquatchCut.core.exporter import (
    ExportJob,
    ExportPartPlacement,
    ExportSheet,
    export_nesting_to_dxf,
)


class TestDXFExport:
    """Test DXF export functionality."""

    @pytest.fixture
    def sample_export_job(self):
        """Create a sample export job for testing."""
        parts = [
            ExportPartPlacement(
                part_id="Door_Panel",
                sheet_index=0,
                x_mm=50.0,
                y_mm=100.0,
                width_mm=600.0,
                height_mm=800.0,
                rotation_deg=0,
                geometry_type="rectangular",
            ),
            ExportPartPlacement(
                part_id="Shelf",
                sheet_index=0,
                x_mm=700.0,
                y_mm=100.0,
                width_mm=400.0,
                height_mm=300.0,
                rotation_deg=90,
                geometry_type="rectangular",
            ),
        ]
        sheet = ExportSheet(0, 1220, 2440, parts)
        return ExportJob("Kitchen Cabinet", "imperial", [sheet])

    def test_dxf_export_handles_empty_job(self, tmp_path):
        """Test that DXF export handles empty jobs gracefully."""
        empty_job = ExportJob("Empty", "imperial", [])

        output_path = tmp_path / "empty_export.dxf"
        result_paths = export_nesting_to_dxf(empty_job, str(output_path))

        assert result_paths == []

    def test_dxf_export_handles_none_job(self, tmp_path):
        """Test that DXF export handles None job gracefully."""
        output_path = tmp_path / "none_export.dxf"
        result_paths = export_nesting_to_dxf(None, str(output_path))

        assert result_paths == []

    def test_dxf_export_requires_import_dxf(self, sample_export_job, tmp_path):
        """Test that DXF export fails gracefully when importDXF is not available."""
        output_path = tmp_path / "test_export.dxf"

        def mock_import(name, *args, **kwargs):
            if name == "importDXF":
                raise ImportError("No module named 'importDXF'")
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError, match="DXF export not available"):
                export_nesting_to_dxf(sample_export_job, str(output_path))

    def test_dxf_export_requires_freecad_app(self, sample_export_job, tmp_path):
        """Test that DXF export fails gracefully when FreeCAD App is not available."""
        output_path = tmp_path / "test_export.dxf"

        def mock_import(name, *args, **kwargs):
            if name == "importDXF":
                return MagicMock()
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("SquatchCut.core.exporter.App", None):
                with pytest.raises(RuntimeError, match="FreeCAD App module not available"):
                    export_nesting_to_dxf(sample_export_job, str(output_path))

    def test_dxf_export_creates_files_successfully(self, sample_export_job, tmp_path):
        """Test that DXF export creates files when all dependencies are available."""
        output_path = tmp_path / "test_export.dxf"

        mock_import_dxf = MagicMock()
        mock_app = MagicMock()
        mock_doc = MagicMock()
        mock_doc.Name = "TestDoc"
        mock_app.newDocument.return_value = mock_doc

        def mock_import(name, *args, **kwargs):
            if name == "importDXF":
                return mock_import_dxf
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("SquatchCut.core.exporter.App", mock_app):
                with patch("SquatchCut.core.exporter.Part") as mock_part:
                    mock_part.makePlane.return_value = MagicMock()

                    result_paths = export_nesting_to_dxf(sample_export_job, str(output_path))

                    assert isinstance(result_paths, list)
                    assert len(result_paths) == 1
                    assert result_paths[0].name == "test_export_S1.dxf"

                    mock_import_dxf.export.assert_called_once()
                    mock_app.closeDocument.assert_called_once_with(mock_doc.Name)

    def test_dxf_export_multi_sheet(self, tmp_path):
        """Test DXF export with multiple sheets."""
        parts1 = [ExportPartPlacement("Part_A", 0, 0, 0, 600, 800, 0)]
        parts2 = [ExportPartPlacement("Part_B", 1, 100, 100, 400, 600, 0)]

        sheets = [
            ExportSheet(0, 1220, 2440, parts1),
            ExportSheet(1, 1220, 2440, parts2),
        ]
        multi_sheet_job = ExportJob("Multi Sheet", "metric", sheets)

        mock_import_dxf = MagicMock()
        mock_app = MagicMock()
        mock_doc = MagicMock()
        mock_doc.Name = "TestDoc"
        mock_app.newDocument.return_value = mock_doc

        def mock_import(name, *args, **kwargs):
            if name == "importDXF":
                return mock_import_dxf
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("SquatchCut.core.exporter.App", mock_app):
                with patch("SquatchCut.core.exporter.Part") as mock_part:
                    mock_part.makePlane.return_value = MagicMock()

                    output_path = tmp_path / "multi_sheet.dxf"
                    result_paths = export_nesting_to_dxf(multi_sheet_job, str(output_path))

                    assert len(result_paths) == 2
                    assert result_paths[0].name == "multi_sheet_S1.dxf"
                    assert result_paths[1].name == "multi_sheet_S2.dxf"

                    assert mock_import_dxf.export.call_count == 2

    def test_dxf_export_handles_export_failure(self, sample_export_job, tmp_path):
        """Test that DXF export handles export failures gracefully."""
        output_path = tmp_path / "failed_export.dxf"

        mock_import_dxf = MagicMock()
        mock_import_dxf.export.side_effect = OSError("Export failed")
        mock_app = MagicMock()
        mock_doc = MagicMock()
        mock_doc.Name = "TestDoc"
        mock_app.newDocument.return_value = mock_doc

        def mock_import(name, *args, **kwargs):
            if name == "importDXF":
                return mock_import_dxf
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("SquatchCut.core.exporter.App", mock_app):
                with patch("SquatchCut.core.exporter.Part") as mock_part:
                    mock_part.makePlane.return_value = MagicMock()

                    with pytest.raises(OSError, match="Export failed"):
                        export_nesting_to_dxf(sample_export_job, str(output_path))

                    mock_app.closeDocument.assert_called_once_with(mock_doc.Name)

    def test_dxf_export_with_complex_geometry(self, tmp_path):
        """Test DXF export with complex geometry parts."""
        mock_complex_geom = MagicMock()
        mock_complex_geom.contour_points = [
            (0, 0),
            (100, 0),
            (100, 50),
            (50, 100),
            (0, 100),
        ]
        mock_complex_geom.apply_kerf.return_value = mock_complex_geom

        parts = [
            ExportPartPlacement(
                part_id="Complex_Shape",
                sheet_index=0,
                x_mm=50.0,
                y_mm=100.0,
                width_mm=100.0,
                height_mm=100.0,
                rotation_deg=0,
                geometry_type="complex",
                complex_geometry=mock_complex_geom,
                kerf_compensation=1.5,
            )
        ]
        sheet = ExportSheet(0, 1220, 2440, parts)
        complex_job = ExportJob("Complex Shapes", "metric", [sheet])

        mock_import_dxf = MagicMock()
        mock_app = MagicMock()
        mock_doc = MagicMock()
        mock_doc.Name = "TestDoc"
        mock_app.newDocument.return_value = mock_doc
        mock_app.Vector.side_effect = lambda x, y, z: (x, y, z)

        def mock_import(name, *args, **kwargs):
            if name == "importDXF":
                return mock_import_dxf
            return __import__(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with patch("SquatchCut.core.exporter.App", mock_app):
                with patch("SquatchCut.core.exporter.Part") as mock_part:
                    mock_part.makePlane.return_value = MagicMock()
                    mock_part.makeLine.return_value = MagicMock()
                    mock_part.Wire.return_value = MagicMock()

                    output_path = tmp_path / "complex_export.dxf"
                    result_paths = export_nesting_to_dxf(complex_job, str(output_path))

                    assert len(result_paths) == 1
                    mock_part.Wire.assert_called()
                    mock_complex_geom.apply_kerf.assert_called_with(1.5)
