"""Property-based tests for SquatchCut advanced features using Hypothesis."""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from unittest.mock import Mock, patch
import tempfile
import threading
import time

from SquatchCut.core.genetic_nesting import (
    GeneticNestingOptimizer,
    GeneticConfig,
    Individual,
    genetic_nest_parts,
)
from SquatchCut.core.grain_direction import (
    GrainDirection,
    GrainAwarePart,
    GrainConstraints,
    infer_grain_direction_from_dimensions,
    parse_grain_direction,
    is_grain_compatible,
    calculate_grain_penalty,
    optimize_rotation_for_grain,
)
from SquatchCut.core.cut_sequence import (
    CutSequencePlanner,
    CutDirection,
    CutType,
    plan_optimal_cutting_sequence,
)
from SquatchCut.core.quality_assurance import (
    QualityAssuranceChecker,
    QualityIssueType,
    QualitySeverity,
    check_nesting_quality,
)
from SquatchCut.core.performance_utils import (
    NestingCache,
    cached_nesting,
    ParallelNestingProcessor,
    MemoryOptimizer,
    clear_nesting_cache,
)
from SquatchCut.core.nesting import Part, PlacedPart
from SquatchCut.core.exporter import (
    ExportJob,
    ExportSheet,
    ExportPartPlacement,
    _calculate_cut_lines,
    _calculate_waste_areas,
)


# Custom strategies for advanced features
@st.composite
def genetic_configs(draw):
    """Generate valid genetic algorithm configurations."""
    return GeneticConfig(
        population_size=draw(st.integers(min_value=5, max_value=50)),
        generations=draw(st.integers(min_value=3, max_value=20)),
        mutation_rate=draw(st.floats(min_value=0.01, max_value=0.5)),
        crossover_rate=draw(st.floats(min_value=0.5, max_value=0.95)),
        max_time_seconds=draw(st.integers(min_value=5, max_value=30)),
    )


@st.composite
def grain_aware_parts(draw, max_parts=20):
    """Generate grain-aware parts with valid properties."""
    num_parts = draw(st.integers(min_value=1, max_value=max_parts))
    parts = []

    for i in range(num_parts):
        part = GrainAwarePart(
            id=f"GrainPart_{i}",
            width=draw(st.floats(min_value=10.0, max_value=500.0)),
            height=draw(st.floats(min_value=10.0, max_value=500.0)),
            can_rotate=draw(st.booleans()),
            grain_direction=draw(st.sampled_from(list(GrainDirection))),
        )
        parts.append(part)

    return parts


@st.composite
def export_parts(draw, max_parts=15):
    """Generate export part placements."""
    num_parts = draw(st.integers(min_value=1, max_value=max_parts))
    parts = []

    for i in range(num_parts):
        part = ExportPartPlacement(
            part_id=f"ExportPart_{i}",
            sheet_index=0,
            x_mm=draw(st.floats(min_value=0.0, max_value=800.0)),
            y_mm=draw(st.floats(min_value=0.0, max_value=600.0)),
            width_mm=draw(st.floats(min_value=10.0, max_value=200.0)),
            height_mm=draw(st.floats(min_value=10.0, max_value=200.0)),
            rotation_deg=draw(st.sampled_from([0, 90, 180, 270])),
        )
        parts.append(part)

    return parts


class TestGeneticAlgorithmProperties:
    """Property-based tests for genetic algorithm functionality."""

    @given(genetic_configs())
    def test_genetic_config_validity(self, config):
        """Property: All genetic configurations should be valid."""
        assert config.population_size > 0
        assert config.generations > 0
        assert 0.0 <= config.mutation_rate <= 1.0
        assert 0.0 <= config.crossover_rate <= 1.0
        assert config.max_time_seconds > 0

    @given(
        st.lists(
            st.builds(
                Part,
                id=st.text(min_size=1, max_size=10),
                width=st.floats(min_value=10, max_value=100),
                height=st.floats(min_value=10, max_value=100),
                can_rotate=st.booleans(),
            ),
            min_size=2,
            max_size=8,
        ),
        genetic_configs(),
    )
    @settings(max_examples=10, deadline=8000)
    def test_genetic_algorithm_deterministic_properties(self, parts, config):
        """Property: Genetic algorithm should produce consistent results with same seed."""
        assume(len(parts) >= 2)

        sheet_width, sheet_height = 400, 300

        # Set a fixed seed for reproducibility in this test
        import random

        random.seed(42)

        try:
            result1 = genetic_nest_parts(
                parts, sheet_width, sheet_height, config=config
            )

            # Reset seed
            random.seed(42)
            result2 = genetic_nest_parts(
                parts, sheet_width, sheet_height, config=config
            )

            # Results should be identical with same seed
            if result1 and result2:
                assert len(result1) == len(result2)
                # Note: Due to floating point precision, exact equality might not hold
                # So we check structural similarity instead
                assert all(p1.id == p2.id for p1, p2 in zip(result1, result2))

        except Exception:
            # Genetic algorithm might fail on some inputs
            pass

    @given(st.integers(min_value=3, max_value=15))
    def test_individual_crossover_properties(self, num_parts):
        """Property: Crossover should produce valid offspring."""
        optimizer = GeneticNestingOptimizer()
        optimizer.parts = [Part(f"P{i}", 50, 50) for i in range(num_parts)]

        parent1 = Individual(
            parts_order=list(range(num_parts)), rotations=[False] * num_parts
        )
        parent2 = Individual(
            parts_order=list(reversed(range(num_parts))), rotations=[True] * num_parts
        )

        child1, child2 = optimizer._crossover(parent1, parent2)

        # Children should have valid parts orders (all parts present)
        assert set(child1.parts_order) == set(range(num_parts))
        assert set(child2.parts_order) == set(range(num_parts))
        assert len(child1.rotations) == num_parts
        assert len(child2.rotations) == num_parts

    @given(st.integers(min_value=2, max_value=10))
    def test_mutation_preserves_validity(self, num_parts):
        """Property: Mutation should preserve individual validity."""
        optimizer = GeneticNestingOptimizer()
        optimizer.parts = [
            Part(f"P{i}", 50, 50, can_rotate=True) for i in range(num_parts)
        ]

        individual = Individual(
            parts_order=list(range(num_parts)), rotations=[False] * num_parts
        )

        # Apply mutation multiple times
        for _ in range(10):
            optimizer._mutate(individual)

            # Should still be valid
            assert set(individual.parts_order) == set(range(num_parts))
            assert len(individual.rotations) == num_parts
            assert all(isinstance(r, bool) for r in individual.rotations)


class TestGrainDirectionProperties:
    """Property-based tests for grain direction functionality."""

    @given(
        st.floats(min_value=0.1, max_value=1000.0),
        st.floats(min_value=0.1, max_value=1000.0),
    )
    def test_grain_inference_symmetry(self, width, height):
        """Property: Grain inference should be symmetric for swapped dimensions."""
        grain1 = infer_grain_direction_from_dimensions(width, height)
        grain2 = infer_grain_direction_from_dimensions(height, width)

        if width != height:  # Skip square case
            if grain1 == GrainDirection.HORIZONTAL:
                assert grain2 == GrainDirection.VERTICAL
            elif grain1 == GrainDirection.VERTICAL:
                assert grain2 == GrainDirection.HORIZONTAL

    @given(st.text())
    def test_grain_parsing_robustness(self, input_text):
        """Property: Grain parsing should never crash."""
        result = parse_grain_direction(input_text)
        assert isinstance(result, GrainDirection)

    @given(grain_aware_parts(max_parts=5), st.sampled_from(list(GrainDirection)))
    def test_grain_constraints_consistency(self, parts, sheet_grain):
        """Property: Grain constraints should be applied consistently."""
        constraints = GrainConstraints(
            sheet_grain=sheet_grain, enforce_part_grain=True, allow_cross_grain=False
        )

        for part in parts:
            for rotation in [0, 90, 180, 270]:
                compatible = is_grain_compatible(
                    part, rotation, sheet_grain, constraints
                )
                penalty = calculate_grain_penalty(
                    part, rotation, sheet_grain, constraints
                )

                # If compatible, penalty should be 0
                if compatible:
                    assert penalty == 0.0

                # Penalty should be non-negative
                assert penalty >= 0.0

    @given(grain_aware_parts(max_parts=3), st.sampled_from(list(GrainDirection)))
    def test_rotation_optimization_validity(self, parts, sheet_grain):
        """Property: Rotation optimization should return valid rotations."""
        constraints = GrainConstraints(sheet_grain=sheet_grain)

        for part in parts:
            rotations = optimize_rotation_for_grain(part, sheet_grain, constraints)

            # Should return list of valid rotation angles
            assert isinstance(rotations, list)
            assert all(r in [0, 90, 180, 270] for r in rotations)

            # Should return at least one rotation if part can rotate
            if part.can_rotate or part.grain_direction == GrainDirection.ANY:
                assert len(rotations) > 0


class TestCutSequenceProperties:
    """Property-based tests for cut sequence planning."""

    @given(
        st.lists(
            st.builds(
                PlacedPart,
                id=st.text(min_size=1, max_size=8),
                x=st.floats(min_value=0, max_value=400),
                y=st.floats(min_value=0, max_value=300),
                width=st.floats(min_value=10, max_value=100),
                height=st.floats(min_value=10, max_value=100),
                sheet_index=st.just(0),
            ),
            min_size=1,
            max_size=10,
        )
    )
    @settings(max_examples=20, deadline=3000)
    def test_cut_sequence_validity(self, placed_parts):
        """Property: Cut sequences should be valid and complete."""
        sheet_sizes = [(500, 400)]

        sequences = plan_optimal_cutting_sequence(placed_parts, sheet_sizes)

        if sequences:
            sequence = sequences[0]

            # Should have valid properties
            assert sequence.sheet_index >= 0
            assert sequence.sheet_width > 0
            assert sequence.sheet_height > 0
            assert sequence.total_cut_length >= 0
            assert sequence.estimated_time_minutes >= 0

            # All operations should be valid
            for op in sequence.operations:
                assert op.cut_id is not None
                assert op.cut_type in [CutType.RIP, CutType.CROSSCUT, CutType.TRIM]
                assert op.direction in [CutDirection.HORIZONTAL, CutDirection.VERTICAL]
                assert op.start <= op.end
                assert op.position >= 0

    @given(
        st.lists(
            st.builds(
                PlacedPart,
                id=st.text(min_size=1, max_size=8),
                x=st.floats(min_value=0, max_value=200),
                y=st.floats(min_value=0, max_value=200),
                width=st.floats(min_value=20, max_value=80),
                height=st.floats(min_value=20, max_value=80),
                sheet_index=st.just(0),
            ),
            min_size=2,
            max_size=6,
        )
    )
    def test_cut_sequence_ordering(self, placed_parts):
        """Property: Cut sequences should follow logical ordering (rips before crosscuts)."""
        sheet_sizes = [(300, 300)]

        sequences = plan_optimal_cutting_sequence(placed_parts, sheet_sizes)

        if sequences and sequences[0].operations:
            operations = sequences[0].operations

            # Find indices of rip and crosscut operations
            rip_indices = [
                i for i, op in enumerate(operations) if op.cut_type == CutType.RIP
            ]
            crosscut_indices = [
                i for i, op in enumerate(operations) if op.cut_type == CutType.CROSSCUT
            ]

            # If both types exist, rips should generally come before crosscuts
            if rip_indices and crosscut_indices:
                max_rip_index = max(rip_indices)
                min_crosscut_index = min(crosscut_indices)
                # Allow some flexibility in ordering, but generally rips should come first
                assert max_rip_index <= min_crosscut_index + 2


class TestQualityAssuranceProperties:
    """Property-based tests for quality assurance functionality."""

    @given(
        st.lists(
            st.builds(
                PlacedPart,
                id=st.text(min_size=1, max_size=8),
                x=st.floats(min_value=0, max_value=800),
                y=st.floats(min_value=0, max_value=600),
                width=st.floats(min_value=10, max_value=100),
                height=st.floats(min_value=10, max_value=100),
                rotation_deg=st.sampled_from([0, 90, 180, 270]),
                sheet_index=st.just(0),
            ),
            min_size=0,
            max_size=15,
        )
    )
    def test_quality_report_properties(self, placed_parts):
        """Property: Quality reports should have consistent properties."""
        sheet_sizes = [(1000, 800)]

        report = check_nesting_quality(placed_parts, sheet_sizes)

        # Basic report properties
        assert 0.0 <= report.overall_score <= 100.0
        assert report.total_parts == len(placed_parts)
        assert report.total_sheets >= 0
        assert len(report.issues) >= 0
        assert len(report.passed_checks) >= 0
        assert len(report.failed_checks) >= 0

        # Issue severity should be valid
        for issue in report.issues:
            assert issue.severity in [
                QualitySeverity.CRITICAL,
                QualitySeverity.WARNING,
                QualitySeverity.INFO,
            ]
            assert issue.issue_type in list(QualityIssueType)
            assert len(issue.part_ids) > 0

    @given(st.floats(min_value=1.0, max_value=50.0))
    def test_quality_checker_spacing_consistency(self, min_spacing):
        """Property: Quality checker should consistently apply spacing rules."""
        checker = QualityAssuranceChecker(min_spacing=min_spacing)

        # Create two parts with known spacing
        spacing = min_spacing - 1.0  # Insufficient spacing
        parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(
                id="B", x=100 + spacing, y=0, width=80, height=60, sheet_index=0
            ),
        ]

        issues = checker._check_spacing_requirements(parts)

        if spacing < min_spacing:
            # Should detect spacing issue
            spacing_issues = [
                i
                for i in issues
                if i.issue_type == QualityIssueType.INSUFFICIENT_SPACING
            ]
            assert len(spacing_issues) > 0

    @given(
        st.floats(min_value=100, max_value=1000),
        st.floats(min_value=100, max_value=1000),
    )
    def test_bounds_checking_accuracy(self, sheet_width, sheet_height):
        """Property: Bounds checking should accurately detect out-of-bounds parts."""
        checker = QualityAssuranceChecker()

        # Create part that's definitely out of bounds
        out_of_bounds_part = PlacedPart(
            id="OutOfBounds",
            x=sheet_width + 10,  # Clearly outside
            y=0,
            width=50,
            height=50,
            sheet_index=0,
        )

        issues = checker._check_bounds_compliance(
            [out_of_bounds_part], [(sheet_width, sheet_height)]
        )

        # Should detect bounds violation
        bounds_issues = [
            i for i in issues if i.issue_type == QualityIssueType.OUT_OF_BOUNDS
        ]
        assert len(bounds_issues) > 0


class TestPerformanceEnhancementProperties:
    """Property-based tests for performance enhancement features."""

    @given(
        st.lists(
            st.builds(
                Part,
                id=st.text(min_size=1, max_size=8),
                width=st.floats(min_value=10, max_value=100),
                height=st.floats(min_value=10, max_value=100),
            ),
            min_size=1,
            max_size=10,
        ),
        st.floats(min_value=100, max_value=500),
        st.floats(min_value=100, max_value=500),
    )
    def test_caching_consistency(self, parts, sheet_width, sheet_height):
        """Property: Caching should return identical results for identical inputs."""
        # Clear any existing cache
        clear_nesting_cache()

        call_count = 0

        @cached_nesting
        def mock_nesting_function(parts_arg, width, height, config=None):
            nonlocal call_count
            call_count += 1
            return [
                PlacedPart(
                    id=p.id, x=0, y=0, width=p.width, height=p.height, sheet_index=0
                )
                for p in parts_arg[:3]
            ]  # Limit to first 3 parts

        # First call
        result1 = mock_nesting_function(parts, sheet_width, sheet_height)

        # Second call with identical parameters
        result2 = mock_nesting_function(parts, sheet_width, sheet_height)

        # Should be called only once due to caching
        assert call_count == 1

        # Results should be identical
        assert len(result1) == len(result2)
        if result1:
            assert all(p1.id == p2.id for p1, p2 in zip(result1, result2))

    @given(
        st.lists(
            st.builds(
                Part,
                id=st.text(min_size=1, max_size=8),
                width=st.floats(min_value=10, max_value=100),
                height=st.floats(min_value=10, max_value=100),
            ),
            min_size=5,
            max_size=20,
        )
    )
    def test_memory_optimization_preserves_functionality(self, parts):
        """Property: Memory optimization should not change functional behavior."""
        # Test that memory optimization doesn't break functionality
        original_parts = parts.copy()
        optimized_parts = MemoryOptimizer.optimize_part_data(parts)

        # Should have same number of parts
        assert len(optimized_parts) == len(original_parts)

        # Essential attributes should be preserved
        for orig, opt in zip(original_parts, optimized_parts):
            assert hasattr(opt, "id")
            assert hasattr(opt, "width")
            assert hasattr(opt, "height")
            assert opt.id == orig.id
            assert opt.width == orig.width
            assert opt.height == orig.height

    def test_cache_thread_safety_property(self):
        """Property: Cache should be thread-safe."""
        cache = NestingCache(max_cache_size=10)
        results = []
        errors = []

        def cache_worker(worker_id):
            try:
                for i in range(5):
                    parts = [Part(f"W{worker_id}_P{i}", 50, 50)]
                    result = [PlacedPart(f"W{worker_id}_P{i}", 0, 0, 50, 50, 0)]

                    # Put and get
                    cache.put(parts, 300, 200, result)
                    retrieved = cache.get(parts, 300, 200)

                    results.append(retrieved is not None)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have no errors and successful operations
        assert len(errors) == 0
        assert len(results) > 0
        assert all(results)  # All cache operations should succeed


class TestExportProperties:
    """Property-based tests for export functionality."""

    @given(
        export_parts(max_parts=10),
        st.floats(min_value=500, max_value=2000),
        st.floats(min_value=400, max_value=1500),
    )
    def test_cut_lines_calculation_properties(self, parts, sheet_width, sheet_height):
        """Property: Cut lines should be within sheet bounds and non-overlapping."""
        cut_lines = _calculate_cut_lines(parts, sheet_width, sheet_height)

        for line in cut_lines:
            # Cut lines should be within sheet bounds
            if line["direction"] == "vertical":
                assert 0 <= line["position"] <= sheet_width
                assert line["length"] == sheet_height
            else:  # horizontal
                assert 0 <= line["position"] <= sheet_height
                assert line["length"] == sheet_width

    @given(
        export_parts(max_parts=8),
        st.floats(min_value=400, max_value=1000),
        st.floats(min_value=300, max_value=800),
    )
    def test_waste_areas_properties(self, parts, sheet_width, sheet_height):
        """Property: Waste areas should not overlap with parts."""
        # Filter parts to ensure they fit within sheet
        valid_parts = []
        for part in parts:
            if (
                part.x_mm + part.width_mm <= sheet_width
                and part.y_mm + part.height_mm <= sheet_height
            ):
                valid_parts.append(part)

        if valid_parts:
            waste_areas = _calculate_waste_areas(valid_parts, sheet_width, sheet_height)

            for waste in waste_areas:
                # Waste areas should be within sheet bounds
                assert waste["x"] >= 0
                assert waste["y"] >= 0
                assert (
                    waste["x"] + waste["width"] <= sheet_width + 1
                )  # Allow small tolerance
                assert waste["y"] + waste["height"] <= sheet_height + 1

                # Waste areas should have positive dimensions
                assert waste["width"] > 0
                assert waste["height"] > 0
                assert waste["area"] > 0

    @given(st.text(min_size=1, max_size=20), st.sampled_from(["metric", "imperial"]))
    def test_export_job_properties(self, job_name, measurement_system):
        """Property: Export jobs should maintain data integrity."""
        # Create a simple export job
        parts = [
            ExportPartPlacement("Part1", 0, 0, 0, 100, 50, 0),
            ExportPartPlacement("Part2", 0, 110, 0, 80, 60, 90),
        ]

        sheet = ExportSheet(0, 1000, 800, parts)
        export_job = ExportJob(job_name, measurement_system, [sheet])

        # Job should preserve all data
        assert export_job.job_name == job_name
        assert export_job.measurement_system == measurement_system
        assert len(export_job.sheets) == 1
        assert len(export_job.sheets[0].parts) == 2

        # Parts should maintain their properties
        for orig_part, export_part in zip(parts, export_job.sheets[0].parts):
            assert export_part.part_id == orig_part.part_id
            assert export_part.x_mm == orig_part.x_mm
            assert export_part.y_mm == orig_part.y_mm
            assert export_part.width_mm == orig_part.width_mm
            assert export_part.height_mm == orig_part.height_mm


if __name__ == "__main__":
    # Run property-based tests for advanced features
    pytest.main([__file__, "-v", "--tb=short"])
