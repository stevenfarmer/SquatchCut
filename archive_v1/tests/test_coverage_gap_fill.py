"""Test file to improve coverage for core logic in session_state and nesting."""

import pytest
from SquatchCut.core import nesting, session_state
from SquatchCut.core.nesting import NestingValidationError, Part, PlacedPart


class TestSessionStateCoverage:
    """Tests for session_state.py coverage gaps."""

    def test_sheet_helpers(self):
        """Cover safe_float, safe_int, normalize_sheet_entry branches."""
        assert session_state._safe_float("invalid") is None
        assert session_state._safe_int("invalid") == 1

        # Test object with attributes (not dict)
        class Entry:
            width_mm = 100
            height_mm = 200
            quantity = 2
            label = "Test"

        norm = session_state._normalize_sheet_entry(Entry())
        assert norm["width_mm"] == 100
        assert norm["height_mm"] == 200
        assert norm["quantity"] == 2
        assert norm["label"] == "Test"

    def test_update_job_sheet(self):
        """Cover update_job_sheet branches."""
        session_state.clear_job_sheets()
        session_state.add_job_sheet(100, 100)

        assert session_state.update_job_sheet(0, width_mm=200, height_mm=200, quantity=5, label="Updated") is True
        assert session_state.update_job_sheet(99, width_mm=200) is False

        sheet = session_state.get_job_sheets()[0]
        assert sheet["width_mm"] == 200
        assert sheet["label"] == "Updated"

    def test_remove_job_sheet(self):
        """Cover remove_job_sheet branches."""
        session_state.clear_job_sheets()
        session_state.add_job_sheet(100, 100)
        assert session_state.remove_job_sheet(99) is False
        assert session_state.remove_job_sheet(0) is True
        assert len(session_state.get_job_sheets()) == 0

    def test_sheet_mode_accessors(self):
        """Cover set_sheet_mode branches."""
        session_state.set_sheet_mode("job_sheets")
        assert session_state.is_job_sheets_mode() is True
        session_state.set_sheet_mode("invalid")
        assert session_state.is_simple_sheet_mode() is True

    def test_job_allow_rotate(self):
        """Cover set/get job_allow_rotate."""
        session_state.set_job_allow_rotate(None)
        assert session_state.get_job_allow_rotate() is None
        session_state.set_job_allow_rotate(True)
        assert session_state.get_job_allow_rotate() is True

    def test_allowed_rotations(self):
        """Cover allowed rotations parsing."""
        session_state.set_allowed_rotations_deg(None)
        assert session_state.get_allowed_rotations_deg() == (0,)
        session_state.set_allowed_rotations_deg("invalid")
        assert session_state.get_allowed_rotations_deg() == (0,)

    def test_nesting_stats(self):
        """Cover nesting stats."""
        session_state.set_nesting_stats() # Defaults
        stats = session_state.get_nesting_stats()
        assert stats["sheets_used"] is None

        session_state.set_nesting_stats(sheets_used=5, cut_complexity=10.0, overlaps_count=0)
        stats = session_state.get_nesting_stats()
        assert stats["sheets_used"] == 5

    def test_panels_accessors(self):
        """Cover panels add/clear."""
        session_state.clear_panels()
        session_state.add_panels([{"id": "p1"}])
        assert len(session_state.get_panels()) == 1
        session_state.add_panels(None)
        assert len(session_state.get_panels()) == 1

    def test_optimization_mode(self):
        """Cover optimization mode fallback."""
        session_state.set_optimization_mode("invalid")
        assert session_state.get_optimization_mode() == "material"

        session_state.set_nesting_mode("invalid")
        assert session_state.get_nesting_mode() == "pack"

    def test_export_flags(self):
        """Cover export flags."""
        session_state.set_export_include_labels(False)
        assert session_state.get_export_include_labels() is False
        session_state.set_export_include_dimensions(True)
        assert session_state.get_export_include_dimensions() is True

    def test_cut_sequence_settings(self):
        """Cover cut sequence settings."""
        session_state.set_generate_cut_sequence(True)
        assert session_state.get_generate_cut_sequence() is True

        session_state.set_cut_sequences(None)
        assert session_state.get_cut_sequences() == []


class TestNestingCoverage:
    """Tests for nesting.py coverage gaps."""

    def test_get_sheet_entry_field(self):
        """Cover _get_sheet_entry_field branches."""
        assert nesting._get_sheet_entry_field(None) is None

        class Entry:
            width = 100

        assert nesting._get_sheet_entry_field(Entry(), "width") == 100
        assert nesting._get_sheet_entry_field(Entry(), "height") is None

    def test_normalize_sheet_definition_invalid(self):
        """Cover invalid sheet definitions."""
        assert nesting._normalize_sheet_definition({}) is None
        assert nesting._normalize_sheet_definition({"width": 0, "height": 100}) is None
        assert nesting._normalize_sheet_definition({"width": 100, "height": "invalid"}) is None

        res = nesting._normalize_sheet_definition({"width": 100, "height": 100, "quantity": "invalid"})
        assert res["quantity"] == 1

    def test_expand_sheet_sizes_empty(self):
        """Cover empty or invalid inputs for expand_sheet_sizes."""
        assert nesting.expand_sheet_sizes(None) == []
        assert nesting.expand_sheet_sizes([{}]) == []

    def test_derive_sheet_sizes_defaults(self):
        """Cover derive_sheet_sizes_for_layout branches."""
        # Simple mode without default sizes
        assert nesting.derive_sheet_sizes_for_layout("simple", [], None, None) == []

        # Simple mode with placements extending count
        placements = [PlacedPart("p1", 0, 0, 0, 10, 10), PlacedPart("p2", 2, 0, 0, 10, 10)] # uses sheet index 2 -> 3 sheets
        sizes = nesting.derive_sheet_sizes_for_layout("simple", [], 100, 100, placements)
        assert len(sizes) == 3

    def test_resolve_sheet_dimensions_edge_cases(self):
        """Cover resolve_sheet_dimensions branches."""
        assert nesting.resolve_sheet_dimensions([], 0, 50, 50) == (50, 50)

        # Index out of bounds uses last valid
        sizes = [(100, 100), (200, 200)]
        assert nesting.resolve_sheet_dimensions(sizes, 5, 0, 0) == (200, 200)

        # fallback if sizes exist but are 0 (unlikely but possible path)
        sizes = [(0, 0)]
        assert nesting.resolve_sheet_dimensions(sizes, 0, 50, 50) == (50, 50)

        # Scan backward
        sizes = [(100, 100), (0, 0)]
        assert nesting.resolve_sheet_dimensions(sizes, 1, 50, 50) == (100, 100)

    def test_nest_rectangular_default_validation(self):
        """Cover validation failure in nest_rectangular_default."""
        parts = [Part("p1", 200, 200)]
        with pytest.raises(ValueError):
            nesting._nest_rectangular_default(parts, 100, 100)

        with pytest.raises(ValueError):
             # 0 sized sheet
             nesting._nest_rectangular_default(parts, 0, 0)

    def test_nest_cut_optimized_edge_cases(self):
        """Cover nest_cut_optimized edge cases."""
        assert nesting.nest_cut_optimized([], 0, 0) == []

        parts = [Part("p1", 200, 200)]
        with pytest.raises(ValueError):
             nesting.nest_cut_optimized(parts, 100, 100)

        # Coverage for rotation fit check
        parts_rot = [Part("p1", 150, 50, can_rotate=True)]
        # Fits if rotated on 100x200 sheet
        res = nesting.nest_cut_optimized(parts_rot, 100, 200)
        assert len(res) == 1
        assert res[0].rotation_deg == 90

    def test_nest_cut_friendly_edge_cases(self):
        """Cover _nest_cut_friendly edge cases."""
        assert nesting._nest_cut_friendly([], 0, 0) == []

        parts = [Part("p1", 200, 200)]
        with pytest.raises(ValueError):
            nesting._nest_cut_friendly(parts, 100, 100)

    def test_estimate_cut_counts_empty(self):
        assert nesting.estimate_cut_counts([])["total"] == 0
        assert nesting.estimate_cut_counts_for_sheets([], [])["total"] == 0

    def test_compute_utilization_empty(self):
        assert nesting.compute_utilization([], 0, 0)["utilization_percent"] == 0
        assert nesting.compute_utilization_for_sheets([], [])["utilization_percent"] == 0

    def test_compute_utilization_for_sheets_details(self):
        placements = [
            PlacedPart("p_zero", 0, 0.0, 0.0, 50.0, 50.0),
            PlacedPart("p_one", 1, 0.0, 0.0, 40.0, 60.0),
            PlacedPart("p_two", 1, 45.0, 0.0, 10.0, 20.0),
        ]
        sheet_sizes = [(100.0, 100.0), (80.0, 120.0)]
        stats = nesting.compute_utilization_for_sheets(placements, sheet_sizes)
        per_sheet = stats["per_sheet_stats"]
        assert stats["sheets_used"] == 2
        assert len(per_sheet) == 2
        assert per_sheet[0]["sheet_index"] == 0
        assert per_sheet[0]["parts_placed"] == 1
        assert per_sheet[0]["placed_area"] == 2500.0
        assert per_sheet[0]["waste_area"] == pytest.approx(10000.0 - 2500.0)
        assert per_sheet[1]["sheet_index"] == 1
        assert per_sheet[1]["parts_placed"] == 2
        assert per_sheet[1]["sheet_area"] == pytest.approx(9600.0)
        assert per_sheet[1]["utilization_percent"] == pytest.approx(
            2600.0 / 9600.0 * 100.0
        )

    def test_analyze_sheet_exhaustion(self):
        res = nesting.analyze_sheet_exhaustion([], [])
        assert res["sheets_used"] == 0

        placements = [PlacedPart("p1", 5, 0, 0, 10, 10)] # Used sheet index 5
        sizes = [(100, 100)] * 2 # Only 2 sheets available
        res = nesting.analyze_sheet_exhaustion(placements, sizes)
        assert res["sheets_exhausted"] is True

    def test_run_shelf_nesting_edge_cases(self):
        assert nesting.run_shelf_nesting(0, 0, []) == []

        panels = [{"width": 100, "height": 100, "qty": 1}]
        # Sheet too small
        res = nesting.run_shelf_nesting(50, 50, panels)
        assert len(res) == 0

        # Invalid panel
        panels = [{"width": 0, "height": 0}]
        res = nesting.run_shelf_nesting(100, 100, panels)
        assert len(res) == 0

    def test_nesting_validation_error(self):
        err = NestingValidationError(100, 100, (nesting.NestingOffendingPart("p1", 200, 200, False),))
        assert "Parts do not fit" in str(err)
