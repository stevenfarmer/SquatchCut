"""Tests for cut sequence planning functionality."""

import pytest
from unittest.mock import Mock, patch

from SquatchCut.core.cut_sequence import (
    CutDirection,
    CutType,
    CutOperation,
    CutSequence,
    CutSequencePlanner,
    plan_optimal_cutting_sequence,
)
from SquatchCut.core.nesting import PlacedPart


class TestCutEnums:
    """Test cut-related enumerations."""

    def test_cut_direction_values(self):
        """Test cut direction enum values."""
        assert CutDirection.HORIZONTAL.value == "horizontal"
        assert CutDirection.VERTICAL.value == "vertical"

    def test_cut_type_values(self):
        """Test cut type enum values."""
        assert CutType.RIP.value == "rip"
        assert CutType.CROSSCUT.value == "crosscut"
        assert CutType.TRIM.value == "trim"


class TestCutOperation:
    """Test cut operation data structure."""

    def test_cut_operation_creation(self):
        """Test creating a cut operation."""
        operation = CutOperation(
            cut_id="RIP_01",
            cut_type=CutType.RIP,
            direction=CutDirection.VERTICAL,
            position=100.0,
            start=0.0,
            end=200.0,
            depth=18.0,
            parts_released=["A", "B"],
            parts_affected=["C"],
            priority=1,
            notes="Test cut",
        )

        assert operation.cut_id == "RIP_01"
        assert operation.cut_type == CutType.RIP
        assert operation.direction == CutDirection.VERTICAL
        assert operation.position == 100.0
        assert operation.start == 0.0
        assert operation.end == 200.0
        assert operation.depth == 18.0
        assert operation.parts_released == ["A", "B"]
        assert operation.parts_affected == ["C"]
        assert operation.priority == 1
        assert operation.notes == "Test cut"

    def test_cut_operation_defaults(self):
        """Test cut operation with default values."""
        operation = CutOperation(
            cut_id="TEST_01",
            cut_type=CutType.CROSSCUT,
            direction=CutDirection.HORIZONTAL,
            position=50.0,
            start=0.0,
            end=100.0,
            depth=18.0,
            parts_released=[],
            parts_affected=[],
        )

        assert operation.priority == 0  # Default
        assert operation.notes == ""  # Default


class TestCutSequence:
    """Test cut sequence data structure."""

    def test_cut_sequence_creation(self):
        """Test creating a cut sequence."""
        operations = [
            CutOperation(
                "RIP_01", CutType.RIP, CutDirection.VERTICAL, 100, 0, 200, 18, [], []
            ),
            CutOperation(
                "CROSS_01",
                CutType.CROSSCUT,
                CutDirection.HORIZONTAL,
                150,
                0,
                300,
                18,
                [],
                [],
            ),
        ]

        sequence = CutSequence(
            sheet_index=0,
            sheet_width=300.0,
            sheet_height=200.0,
            operations=operations,
            total_cut_length=500.0,
            estimated_time_minutes=15.5,
        )

        assert sequence.sheet_index == 0
        assert sequence.sheet_width == 300.0
        assert sequence.sheet_height == 200.0
        assert len(sequence.operations) == 2
        assert sequence.total_cut_length == 500.0
        assert sequence.estimated_time_minutes == 15.5

    def test_cut_sequence_defaults(self):
        """Test cut sequence with default values."""
        sequence = CutSequence(
            sheet_index=0, sheet_width=300.0, sheet_height=200.0, operations=[]
        )

        assert sequence.total_cut_length == 0.0
        assert sequence.estimated_time_minutes == 0.0


class TestCutSequencePlanner:
    """Test cut sequence planner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.planner = CutSequencePlanner(
            kerf_width=3.0, cut_speed_mm_per_min=1000.0, setup_time_per_cut=0.5
        )

        # Create test placed parts
        self.placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=100, y=0, width=80, height=60, sheet_index=0),
            PlacedPart(id="C", x=0, y=50, width=120, height=40, sheet_index=0),
        ]

        self.sheet_sizes = [(300, 200)]

    def test_planner_initialization(self):
        """Test planner initialization."""
        assert self.planner.kerf_width == 3.0
        assert self.planner.cut_speed == 1000.0
        assert self.planner.setup_time == 0.5

    def test_collect_vertical_cuts(self):
        """Test collecting vertical cut positions."""
        cuts = self.planner._collect_vertical_cuts(self.placed_parts, 300, 200)

        # Should include part boundaries
        expected_cuts = [100, 120, 180]  # Right edges of parts A, C, B

        for cut in expected_cuts:
            assert cut in cuts

        # Should be sorted
        assert cuts == sorted(cuts)

    def test_collect_horizontal_cuts(self):
        """Test collecting horizontal cut positions."""
        cuts = self.planner._collect_horizontal_cuts(self.placed_parts, 300, 200)

        # Should include part boundaries
        expected_cuts = [50, 60, 90]  # Top edges of parts A/B, B, C

        for cut in expected_cuts:
            assert cut in cuts

        # Should be sorted
        assert cuts == sorted(cuts)

    def test_plan_rip_cuts(self):
        """Test planning rip cuts (vertical)."""
        cut_positions = [100, 180]
        operations = self.planner._plan_rip_cuts(cut_positions, self.placed_parts, 200)

        assert len(operations) == 2

        # Check first operation
        op1 = operations[0]
        assert op1.cut_type == CutType.RIP
        assert op1.direction == CutDirection.VERTICAL
        assert op1.position == 100
        assert "A" in op1.parts_released  # Part A should be released by this cut

    def test_plan_crosscuts(self):
        """Test planning crosscuts (horizontal)."""
        cut_positions = [50, 90]
        operations = self.planner._plan_crosscuts(cut_positions, self.placed_parts, 300)

        assert len(operations) == 2

        # Check first operation
        op1 = operations[0]
        assert op1.cut_type == CutType.CROSSCUT
        assert op1.direction == CutDirection.HORIZONTAL
        assert op1.position == 50

    def test_plan_sheet_sequence(self):
        """Test planning sequence for a single sheet."""
        sequence = self.planner._plan_sheet_sequence(self.placed_parts, 300, 200, 0)

        assert sequence.sheet_index == 0
        assert sequence.sheet_width == 300
        assert sequence.sheet_height == 200
        assert len(sequence.operations) > 0
        assert sequence.total_cut_length > 0
        assert sequence.estimated_time_minutes > 0

        # Should have both rip cuts and crosscuts
        rip_cuts = [op for op in sequence.operations if op.cut_type == CutType.RIP]
        crosscuts = [
            op for op in sequence.operations if op.cut_type == CutType.CROSSCUT
        ]

        assert len(rip_cuts) > 0
        assert len(crosscuts) > 0

    def test_plan_cutting_sequence_multiple_sheets(self):
        """Test planning sequences for multiple sheets."""
        # Add parts on second sheet
        multi_sheet_parts = self.placed_parts + [
            PlacedPart(id="D", x=0, y=0, width=150, height=75, sheet_index=1)
        ]

        sheet_sizes = [(300, 200), (400, 250)]

        sequences = self.planner.plan_cutting_sequence(multi_sheet_parts, sheet_sizes)

        assert len(sequences) == 2
        assert sequences[0].sheet_index == 0
        assert sequences[1].sheet_index == 1

        # Each sequence should have operations
        for sequence in sequences:
            assert len(sequence.operations) > 0

    def test_optimize_sequence(self):
        """Test sequence optimization."""
        # Create a basic sequence
        original_sequence = self.planner._plan_sheet_sequence(
            self.placed_parts, 300, 200, 0
        )

        # Optimize it
        optimized_sequence = self.planner.optimize_sequence(original_sequence)

        assert optimized_sequence.sheet_index == original_sequence.sheet_index
        assert optimized_sequence.sheet_width == original_sequence.sheet_width
        assert optimized_sequence.sheet_height == original_sequence.sheet_height
        assert len(optimized_sequence.operations) == len(original_sequence.operations)

        # Check that rip cuts come before crosscuts
        rip_indices = []
        crosscut_indices = []

        for i, op in enumerate(optimized_sequence.operations):
            if op.cut_type == CutType.RIP:
                rip_indices.append(i)
            elif op.cut_type == CutType.CROSSCUT:
                crosscut_indices.append(i)

        if rip_indices and crosscut_indices:
            assert max(rip_indices) < min(crosscut_indices)

    def test_generate_cut_report(self):
        """Test generating cut report."""
        sequences = self.planner.plan_cutting_sequence(
            self.placed_parts, self.sheet_sizes
        )
        report = self.planner.generate_cut_report(sequences)

        assert "summary" in report
        assert "sequences" in report
        assert "efficiency_metrics" in report

        summary = report["summary"]
        assert "total_sheets" in summary
        assert "total_cuts" in summary
        assert "total_cut_length_mm" in summary
        assert "estimated_time_minutes" in summary
        assert "rip_cuts" in summary
        assert "crosscuts" in summary

        assert summary["total_sheets"] == len(sequences)
        assert summary["total_cuts"] > 0
        assert summary["total_cut_length_mm"] > 0

    def test_empty_parts_list(self):
        """Test planning with empty parts list."""
        sequences = self.planner.plan_cutting_sequence([], self.sheet_sizes)
        assert len(sequences) == 0

    def test_single_part(self):
        """Test planning with single part."""
        single_part = [
            PlacedPart(id="A", x=50, y=50, width=100, height=80, sheet_index=0)
        ]

        sequences = self.planner.plan_cutting_sequence(single_part, self.sheet_sizes)

        assert len(sequences) == 1
        sequence = sequences[0]

        # Should have cuts to release the part
        assert len(sequence.operations) > 0


class TestCutSequencePlannerEdgeCases:
    """Test edge cases for cut sequence planner."""

    def setup_method(self):
        """Set up test fixtures."""
        self.planner = CutSequencePlanner()

    def test_parts_at_sheet_edges(self):
        """Test parts positioned at sheet edges."""
        parts = [
            PlacedPart(
                id="A", x=0, y=0, width=100, height=50, sheet_index=0
            ),  # At origin
            PlacedPart(
                id="B", x=200, y=150, width=100, height=50, sheet_index=0
            ),  # At far corner
        ]

        sheet_sizes = [(300, 200)]
        sequences = self.planner.plan_cutting_sequence(parts, sheet_sizes)

        assert len(sequences) == 1
        sequence = sequences[0]

        # Should still generate cuts
        assert len(sequence.operations) > 0

    def test_overlapping_parts(self):
        """Test handling overlapping parts."""
        parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=100, sheet_index=0),
            PlacedPart(
                id="B", x=50, y=50, width=100, height=100, sheet_index=0
            ),  # Overlaps A
        ]

        sheet_sizes = [(300, 200)]
        sequences = self.planner.plan_cutting_sequence(parts, sheet_sizes)

        # Should handle gracefully
        assert len(sequences) == 1

    def test_very_small_parts(self):
        """Test handling very small parts."""
        parts = [
            PlacedPart(id="A", x=0, y=0, width=1, height=1, sheet_index=0),
            PlacedPart(id="B", x=10, y=10, width=2, height=2, sheet_index=0),
        ]

        sheet_sizes = [(100, 100)]
        sequences = self.planner.plan_cutting_sequence(parts, sheet_sizes)

        assert len(sequences) == 1
        sequence = sequences[0]

        # Should generate operations even for tiny parts
        assert len(sequence.operations) >= 0


class TestHighLevelFunction:
    """Test high-level cut sequence planning function."""

    def test_plan_optimal_cutting_sequence(self):
        """Test high-level planning function."""
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=100, y=0, width=80, height=60, sheet_index=0),
        ]

        sheet_sizes = [(300, 200)]

        sequences = plan_optimal_cutting_sequence(
            placed_parts, sheet_sizes, kerf_width=3.0
        )

        assert len(sequences) == 1
        sequence = sequences[0]

        assert sequence.sheet_index == 0
        assert len(sequence.operations) > 0
        assert sequence.total_cut_length > 0
        assert sequence.estimated_time_minutes > 0

    @patch("SquatchCut.core.cut_sequence.logger")
    def test_plan_optimal_cutting_sequence_logging(self, mock_logger):
        """Test that planning function logs appropriately."""
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0)
        ]

        sheet_sizes = [(300, 200)]

        plan_optimal_cutting_sequence(placed_parts, sheet_sizes)

        # Should log completion
        mock_logger.info.assert_called()

    def test_plan_with_custom_kerf(self):
        """Test planning with custom kerf width."""
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0)
        ]

        sheet_sizes = [(300, 200)]

        sequences = plan_optimal_cutting_sequence(
            placed_parts, sheet_sizes, kerf_width=5.0
        )

        # Should complete without error
        assert len(sequences) == 1

    def test_plan_empty_input(self):
        """Test planning with empty input."""
        sequences = plan_optimal_cutting_sequence([], [(300, 200)])
        assert len(sequences) == 0


class TestCutSequenceIntegration:
    """Integration tests for cut sequence planning."""

    def test_realistic_layout(self):
        """Test with a realistic nesting layout."""
        # Create a realistic layout with multiple parts
        placed_parts = [
            # Row 1
            PlacedPart(id="Panel_1", x=0, y=0, width=200, height=100, sheet_index=0),
            PlacedPart(id="Panel_2", x=200, y=0, width=150, height=100, sheet_index=0),
            PlacedPart(id="Panel_3", x=350, y=0, width=100, height=100, sheet_index=0),
            # Row 2
            PlacedPart(id="Panel_4", x=0, y=100, width=180, height=80, sheet_index=0),
            PlacedPart(id="Panel_5", x=180, y=100, width=120, height=80, sheet_index=0),
            PlacedPart(id="Panel_6", x=300, y=100, width=150, height=80, sheet_index=0),
        ]

        sheet_sizes = [(500, 250)]  # Standard plywood sheet (scaled down)

        planner = CutSequencePlanner(
            kerf_width=3.2,  # Typical table saw kerf
            cut_speed_mm_per_min=800,  # Conservative cutting speed
            setup_time_per_cut=1.0,  # Time to position and start cut
        )

        sequences = planner.plan_cutting_sequence(placed_parts, sheet_sizes)

        assert len(sequences) == 1
        sequence = sequences[0]

        # Should have reasonable number of cuts
        assert 4 <= len(sequence.operations) <= 20

        # Should have both rip and crosscuts
        rip_cuts = [op for op in sequence.operations if op.cut_type == CutType.RIP]
        crosscuts = [
            op for op in sequence.operations if op.cut_type == CutType.CROSSCUT
        ]

        assert len(rip_cuts) > 0
        assert len(crosscuts) > 0

        # Total cut length should be reasonable
        assert sequence.total_cut_length > 0
        assert sequence.total_cut_length < 5000  # Shouldn't be excessive

        # Time estimate should be reasonable
        assert sequence.estimated_time_minutes > 0
        assert sequence.estimated_time_minutes < 60  # Less than an hour

    def test_multi_sheet_layout(self):
        """Test with multi-sheet layout."""
        placed_parts = [
            # Sheet 1
            PlacedPart(id="A1", x=0, y=0, width=100, height=100, sheet_index=0),
            PlacedPart(id="A2", x=100, y=0, width=100, height=100, sheet_index=0),
            # Sheet 2
            PlacedPart(id="B1", x=0, y=0, width=150, height=75, sheet_index=1),
            PlacedPart(id="B2", x=150, y=0, width=150, height=75, sheet_index=1),
        ]

        sheet_sizes = [(250, 150), (350, 200)]  # Different sheet sizes

        sequences = plan_optimal_cutting_sequence(placed_parts, sheet_sizes)

        assert len(sequences) == 2

        # Each sheet should have its own sequence
        sheet_0_seq = next(s for s in sequences if s.sheet_index == 0)
        sheet_1_seq = next(s for s in sequences if s.sheet_index == 1)

        assert sheet_0_seq.sheet_width == 250
        assert sheet_0_seq.sheet_height == 150
        assert sheet_1_seq.sheet_width == 350
        assert sheet_1_seq.sheet_height == 200

        # Both should have operations
        assert len(sheet_0_seq.operations) > 0
        assert len(sheet_1_seq.operations) > 0

    def test_efficiency_metrics(self):
        """Test that efficiency metrics are reasonable."""
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=100, sheet_index=0),
            PlacedPart(id="B", x=100, y=0, width=100, height=100, sheet_index=0),
            PlacedPart(id="C", x=0, y=100, width=100, height=100, sheet_index=0),
            PlacedPart(id="D", x=100, y=100, width=100, height=100, sheet_index=0),
        ]

        sheet_sizes = [(250, 250)]

        planner = CutSequencePlanner()
        sequences = planner.plan_cutting_sequence(placed_parts, sheet_sizes)
        report = planner.generate_cut_report(sequences)

        metrics = report["efficiency_metrics"]

        # Should have reasonable metrics
        assert metrics["avg_cuts_per_sheet"] > 0
        assert metrics["avg_cut_length_mm"] > 0
        assert metrics["cut_speed_mm_per_min"] == planner.cut_speed
        assert metrics["setup_time_per_cut_min"] == planner.setup_time
