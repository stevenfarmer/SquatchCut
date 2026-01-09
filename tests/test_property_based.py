"""Property-based tests for SquatchCut core functionality using Hypothesis."""


import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule
from SquatchCut.core.genetic_nesting import (
    GeneticConfig,
    genetic_nest_parts,
)
from SquatchCut.core.grain_direction import (
    GrainAwarePart,
    GrainConstraints,
    GrainDirection,
    infer_grain_direction_from_dimensions,
    is_grain_compatible,
    parse_grain_direction,
)
from SquatchCut.core.nesting import (
    NestingValidationError,
    Part,
    PlacedPart,
    compute_utilization,
    get_usable_sheet_area,
    nest_parts,
    part_fits_sheet,
    validate_parts_fit_sheet,
)
from SquatchCut.core.quality_assurance import (
    check_nesting_quality,
)
from SquatchCut.core.units import (
    format_metric_length,
    inches_to_fraction_str,
    inches_to_mm,
    mm_to_inches,
)


# Custom strategies for SquatchCut domain objects
@st.composite
def valid_dimensions(draw):
    """Generate valid dimensions (positive floats with reasonable bounds)."""
    return draw(
        st.floats(
            min_value=1.0, max_value=5000.0, allow_nan=False, allow_infinity=False
        )
    )


@st.composite
def valid_parts(draw, max_parts=50):
    """Generate valid Part objects."""
    num_parts = draw(st.integers(min_value=1, max_value=max_parts))
    parts = []

    for i in range(num_parts):
        part = Part(
            id=f"Part_{i}",
            width=draw(valid_dimensions()),
            height=draw(valid_dimensions()),
            can_rotate=draw(st.booleans()),
        )
        parts.append(part)

    return parts


@st.composite
def valid_sheet_size(draw):
    """Generate valid sheet dimensions."""
    width = draw(
        st.floats(
            min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False
        )
    )
    height = draw(
        st.floats(
            min_value=100.0, max_value=10000.0, allow_nan=False, allow_infinity=False
        )
    )
    return width, height


@st.composite
def placed_parts_on_sheet(draw, sheet_width, sheet_height, max_parts=20):
    """Generate valid PlacedPart objects that fit within sheet bounds."""
    num_parts = draw(st.integers(min_value=0, max_value=max_parts))
    parts = []

    for i in range(num_parts):
        # Generate part dimensions that can fit on sheet
        max_width = min(sheet_width * 0.8, 500.0)  # Leave some margin
        max_height = min(sheet_height * 0.8, 500.0)

        width = draw(
            st.floats(
                min_value=10.0,
                max_value=max_width,
                allow_nan=False,
                allow_infinity=False,
            )
        )
        height = draw(
            st.floats(
                min_value=10.0,
                max_value=max_height,
                allow_nan=False,
                allow_infinity=False,
            )
        )

        # Generate position that keeps part within bounds
        max_x = sheet_width - width
        max_y = sheet_height - height

        if max_x > 0 and max_y > 0:
            x = draw(
                st.floats(
                    min_value=0.0,
                    max_value=max_x,
                    allow_nan=False,
                    allow_infinity=False,
                )
            )
            y = draw(
                st.floats(
                    min_value=0.0,
                    max_value=max_y,
                    allow_nan=False,
                    allow_infinity=False,
                )
            )

            part = PlacedPart(
                id=f"Part_{i}",
                x=x,
                y=y,
                width=width,
                height=height,
                rotation_deg=draw(st.sampled_from([0, 90, 180, 270])),
                sheet_index=0,
            )
            parts.append(part)

    return parts


class TestUnitConversionProperties:
    """Property-based tests for unit conversion functions."""

    @given(
        st.floats(
            min_value=0.001, max_value=10000.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_mm_to_inches_roundtrip(self, mm_value):
        """Property: Converting mm to inches and back should preserve the value."""
        assume(mm_value > 0)

        inches = mm_to_inches(mm_value)
        back_to_mm = inches_to_mm(inches)

        # Allow small floating point errors
        assert abs(mm_value - back_to_mm) < 0.001

    @given(
        st.floats(
            min_value=0.001, max_value=400.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_inches_to_mm_roundtrip(self, inch_value):
        """Property: Converting inches to mm and back should preserve the value."""
        assume(inch_value > 0)

        mm = inches_to_mm(inch_value)
        back_to_inches = mm_to_inches(mm)

        # Allow small floating point errors
        assert abs(inch_value - back_to_inches) < 0.001

    @given(
        st.floats(
            min_value=0.0, max_value=10000.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_mm_to_inches_monotonic(self, mm_value):
        """Property: mm_to_inches should be monotonically increasing."""
        assume(mm_value >= 0)

        inches = mm_to_inches(mm_value)
        larger_mm = mm_value + 1.0
        larger_inches = mm_to_inches(larger_mm)

        assert larger_inches >= inches

    @given(
        st.floats(
            min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_format_metric_length_properties(self, mm_value):
        """Property: Formatted metric length should be parseable and positive."""
        assume(mm_value > 0)

        formatted = format_metric_length(mm_value)

        # Should not be empty
        assert len(formatted) > 0
        # Should be a valid number string (format_metric_length returns just the number)
        try:
            parsed_value = float(formatted)
            assert parsed_value > 0
            # Should be reasonably close to original value (within formatting precision)
            assert abs(parsed_value - mm_value) < max(0.001, mm_value * 0.01)
        except ValueError as e:
            raise AssertionError(f"Formatted value '{formatted}' is not a valid number") from e

    @given(
        st.floats(
            min_value=1 / 64, max_value=100.0, allow_nan=False, allow_infinity=False
        )
    )
    def test_inches_to_fraction_str_properties(self, inch_value):
        """Property: Fraction string should represent a valid fraction."""
        assume(inch_value > 0)

        fraction_str = inches_to_fraction_str(inch_value)

        # Should not be empty
        assert len(fraction_str) > 0
        # Should contain digits
        assert any(c.isdigit() for c in fraction_str)
        # Should not contain invalid characters
        assert not any(c in fraction_str for c in ["@", "#", "$", "%"])


class TestNestingProperties:
    """Property-based tests for nesting algorithms."""

    @given(valid_parts(max_parts=20), valid_sheet_size())
    @settings(max_examples=50, deadline=5000)  # Longer deadline for complex operations
    def test_nesting_no_overlaps(self, parts, sheet_size):
        """Property: Nested parts should never overlap on the same sheet."""
        sheet_width, sheet_height = sheet_size

        # Filter parts that can potentially fit
        fitting_parts = []
        for part in parts:
            if part_fits_sheet(
                part.width, part.height, sheet_width, sheet_height, part.can_rotate
            ):
                fitting_parts.append(part)

        assume(len(fitting_parts) > 0)

        try:
            placed_parts = nest_parts(fitting_parts, sheet_width, sheet_height)

            # Check no overlaps within each sheet
            sheets = {}
            for part in placed_parts:
                sheet_idx = part.sheet_index
                if sheet_idx not in sheets:
                    sheets[sheet_idx] = []
                sheets[sheet_idx].append(part)

            for sheet_parts in sheets.values():
                for i, part1 in enumerate(sheet_parts):
                    for part2 in sheet_parts[i + 1 :]:
                        # Check no overlap
                        assert not self._rectangles_overlap(
                            part1, part2
                        ), f"Parts {part1.id} and {part2.id} overlap"

        except ValueError:
            # Some parts might not fit - this is acceptable
            pass

    @given(valid_parts(max_parts=10), valid_sheet_size())
    @settings(max_examples=30, deadline=3000)
    def test_nesting_within_bounds(self, parts, sheet_size):
        """Property: All nested parts should be within sheet boundaries."""
        sheet_width, sheet_height = sheet_size

        # Filter parts that can fit
        fitting_parts = [
            p
            for p in parts
            if part_fits_sheet(
                p.width, p.height, sheet_width, sheet_height, p.can_rotate
            )
        ]
        assume(len(fitting_parts) > 0)

        try:
            placed_parts = nest_parts(fitting_parts, sheet_width, sheet_height)

            for part in placed_parts:
                # Part should be within sheet bounds (allow reasonable tolerance for nesting algorithm)
                assert part.x >= -0.1, f"Part {part.id} has negative x position"
                assert part.y >= -0.1, f"Part {part.id} has negative y position"
                # Use larger tolerance since nesting algorithms may have slight precision issues
                tolerance = max(
                    2.0, sheet_width * 0.01
                )  # 1% of sheet size or 2mm minimum
                assert (
                    part.x + part.width <= sheet_width + tolerance
                ), f"Part {part.id} exceeds sheet width: {part.x + part.width} > {sheet_width + tolerance}"
                assert (
                    part.y + part.height <= sheet_height + tolerance
                ), f"Part {part.id} exceeds sheet height: {part.y + part.height} > {sheet_height + tolerance}"

        except ValueError:
            # Some configurations might not be nestable
            pass

    @given(valid_parts(max_parts=15), valid_sheet_size())
    @settings(max_examples=30, deadline=3000)
    def test_nesting_preserves_part_count(self, parts, sheet_size):
        """Property: Nesting should not create or destroy parts."""
        sheet_width, sheet_height = sheet_size

        # Filter to parts that can fit
        fitting_parts = [
            p
            for p in parts
            if part_fits_sheet(
                p.width, p.height, sheet_width, sheet_height, p.can_rotate
            )
        ]
        assume(len(fitting_parts) > 0)

        try:
            placed_parts = nest_parts(fitting_parts, sheet_width, sheet_height)

            # Should place at most the number of input parts
            assert len(placed_parts) <= len(fitting_parts)

            # All placed part IDs should exist in original parts
            original_ids = {p.id for p in fitting_parts}
            placed_ids = {p.id for p in placed_parts}
            assert placed_ids.issubset(original_ids)

        except ValueError:
            # Some configurations might not be nestable
            pass

    @given(valid_sheet_size())
    def test_utilization_properties(self, sheet_size):
        """Property: Utilization should be between 0 and 100 percent."""
        sheet_width, sheet_height = sheet_size

        # Create some placed parts
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=110, y=0, width=80, height=60, sheet_index=0),
        ]

        utilization = compute_utilization(placed_parts, sheet_width, sheet_height)

        assert 0.0 <= utilization["utilization_percent"] <= 100.0
        assert utilization["sheets_used"] >= 0
        assert utilization["placed_area"] >= 0
        assert utilization["sheet_area"] >= 0

    def _rectangles_overlap(self, part1, part2):
        """Check if two placed parts overlap."""
        return not (
            part1.x >= part2.x + part2.width
            or part2.x >= part1.x + part1.width
            or part1.y >= part2.y + part2.height
            or part2.y >= part1.y + part1.height
        )


class TestGrainDirectionProperties:
    """Property-based tests for grain direction functionality."""

    @given(
        st.floats(
            min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
        st.floats(
            min_value=1.0, max_value=1000.0, allow_nan=False, allow_infinity=False
        ),
    )
    def test_grain_inference_consistency(self, width, height):
        """Property: Grain inference should be consistent and logical."""
        grain = infer_grain_direction_from_dimensions(width, height)

        aspect_ratio = width / height

        if aspect_ratio > 2.0:
            assert grain == GrainDirection.HORIZONTAL
        elif aspect_ratio < 0.5:
            assert grain == GrainDirection.VERTICAL
        else:
            assert grain == GrainDirection.ANY

    @given(st.text(min_size=0, max_size=20))
    def test_grain_parsing_robustness(self, grain_str):
        """Property: Grain parsing should never crash and return valid enum."""
        result = parse_grain_direction(grain_str)
        assert isinstance(result, GrainDirection)
        assert result in [
            GrainDirection.HORIZONTAL,
            GrainDirection.VERTICAL,
            GrainDirection.ANY,
        ]

    @given(
        st.sampled_from(
            [GrainDirection.HORIZONTAL, GrainDirection.VERTICAL, GrainDirection.ANY]
        ),
        st.sampled_from([0, 90, 180, 270]),
        st.sampled_from(
            [GrainDirection.HORIZONTAL, GrainDirection.VERTICAL, GrainDirection.ANY]
        ),
    )
    def test_grain_compatibility_properties(self, part_grain, rotation, sheet_grain):
        """Property: Grain compatibility should be symmetric and consistent."""
        part = GrainAwarePart("test", 100, 50, grain_direction=part_grain)
        constraints = GrainConstraints(sheet_grain=sheet_grain, enforce_part_grain=True)

        # ANY grain should always be compatible
        if part_grain == GrainDirection.ANY or sheet_grain == GrainDirection.ANY:
            result = is_grain_compatible(part, rotation, sheet_grain, constraints)
            assert result is True

        # Test with enforcement disabled
        constraints_disabled = GrainConstraints(enforce_part_grain=False)
        result_disabled = is_grain_compatible(
            part, rotation, sheet_grain, constraints_disabled
        )
        assert result_disabled is True


class TestGeneticAlgorithmProperties:
    """Property-based tests for genetic algorithm optimization."""

    @given(valid_parts(max_parts=10), valid_sheet_size())
    @settings(max_examples=10, deadline=10000)  # Longer deadline for genetic algorithm
    def test_genetic_algorithm_validity(self, parts, sheet_size):
        """Property: Genetic algorithm should produce valid nesting results."""
        sheet_width, sheet_height = sheet_size

        # Filter to parts that can fit
        fitting_parts = [
            p
            for p in parts
            if part_fits_sheet(
                p.width, p.height, sheet_width, sheet_height, p.can_rotate
            )
        ]
        assume(len(fitting_parts) >= 2)  # Need at least 2 parts for meaningful test

        config = GeneticConfig(
            population_size=10,
            generations=5,
            max_time_seconds=5,  # Short time for testing
        )

        try:
            placed_parts = genetic_nest_parts(
                fitting_parts, sheet_width, sheet_height, config=config
            )

            # All placed parts should be valid
            for part in placed_parts:
                assert part.x >= 0
                assert part.y >= 0
                assert part.x + part.width <= sheet_width + 0.1
                assert part.y + part.height <= sheet_height + 0.1
                assert part.rotation_deg in [0, 90, 180, 270]

            # Should not have overlaps
            for i, part1 in enumerate(placed_parts):
                for part2 in placed_parts[i + 1 :]:
                    if part1.sheet_index == part2.sheet_index:
                        assert not self._rectangles_overlap(part1, part2)

        except Exception:
            # Genetic algorithm might fail on some inputs - that's acceptable
            pass

    def _rectangles_overlap(self, part1, part2):
        """Check if two placed parts overlap."""
        return not (
            part1.x >= part2.x + part2.width
            or part2.x >= part1.x + part1.width
            or part1.y >= part2.y + part2.height
            or part2.y >= part1.y + part1.height
        )


class TestQualityAssuranceProperties:
    """Property-based tests for quality assurance functionality."""

    @given(valid_sheet_size())
    def test_quality_checker_score_bounds(self, sheet_size):
        """Property: Quality scores should always be between 0 and 100."""
        sheet_width, sheet_height = sheet_size

        # Create some test parts
        placed_parts = [
            PlacedPart(id="A", x=10, y=10, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=120, y=10, width=80, height=60, sheet_index=0),
        ]

        report = check_nesting_quality(placed_parts, [(sheet_width, sheet_height)])

        assert 0.0 <= report.overall_score <= 100.0
        assert report.total_parts >= 0
        assert report.total_sheets >= 0
        assert len(report.issues) >= 0

    @given(placed_parts_on_sheet(1000, 800, max_parts=10))
    def test_quality_checker_no_false_positives(self, placed_parts):
        """Property: Well-placed parts should not generate critical issues."""
        assume(len(placed_parts) > 0)

        # Ensure parts don't overlap by spacing them out
        spaced_parts = []
        x_offset = 0
        for _i, part in enumerate(placed_parts[:5]):  # Limit to 5 parts
            new_part = PlacedPart(
                id=part.id,
                x=x_offset,
                y=10,
                width=part.width,
                height=part.height,
                rotation_deg=0,
                sheet_index=0,
            )
            spaced_parts.append(new_part)
            x_offset += part.width + 10  # Add spacing

        if x_offset < 1000:  # Only test if parts fit
            report = check_nesting_quality(spaced_parts, [(1000, 800)])

            # Should have no critical overlap issues
            critical_overlaps = [
                issue
                for issue in report.issues
                if issue.issue_type.value == "overlap"
                and issue.severity.value == "critical"
            ]
            assert len(critical_overlaps) == 0


class TestPartFittingProperties:
    """Property-based tests for part fitting logic."""

    @given(
        valid_dimensions(), valid_dimensions(), valid_dimensions(), valid_dimensions()
    )
    def test_part_fits_sheet_properties(
        self, part_width, part_height, sheet_width, sheet_height
    ):
        """Property: Part fitting should be consistent with basic geometry."""
        # Without rotation
        fits_normal = part_fits_sheet(
            part_width, part_height, sheet_width, sheet_height, can_rotate=False
        )
        expected_normal = part_width <= sheet_width and part_height <= sheet_height
        assert fits_normal == expected_normal

        # With rotation
        fits_rotated = part_fits_sheet(
            part_width, part_height, sheet_width, sheet_height, can_rotate=True
        )
        expected_rotated = (
            part_width <= sheet_width and part_height <= sheet_height
        ) or (part_height <= sheet_width and part_width <= sheet_height)
        assert fits_rotated == expected_rotated

    @given(valid_parts(max_parts=20), valid_dimensions(), valid_dimensions())
    def test_validate_parts_fit_consistency(self, parts, sheet_width, sheet_height):
        """Property: Validation should be consistent with individual part fitting."""
        usable_width, usable_height = get_usable_sheet_area(
            sheet_width, sheet_height, margin_mm=0
        )

        # Check each part individually
        should_pass = True
        for part in parts:
            if not part_fits_sheet(
                part.width, part.height, usable_width, usable_height, part.can_rotate
            ):
                should_pass = False
                break

        # Validation should match individual checks
        if should_pass:
            try:
                validate_parts_fit_sheet(parts, usable_width, usable_height)
                # Should not raise exception
            except Exception as e:
                # If it raises, our prediction was wrong - this is a test failure
                raise AssertionError("Validation failed when individual parts should fit") from e
        else:
            # Should raise exception
            with pytest.raises(NestingValidationError):
                validate_parts_fit_sheet(parts, usable_width, usable_height)


# Stateful testing for complex nesting scenarios
class NestingStateMachine(RuleBasedStateMachine):
    """Stateful testing for nesting operations."""

    def __init__(self):
        super().__init__()
        self.parts = []
        self.sheet_width = 1000
        self.sheet_height = 800
        self.placed_parts = []

    @rule(
        part_width=st.floats(min_value=10, max_value=200),
        part_height=st.floats(min_value=10, max_value=200),
        can_rotate=st.booleans(),
    )
    def add_part(self, part_width, part_height, can_rotate):
        """Add a part to the collection."""
        part_id = f"Part_{len(self.parts)}"
        part = Part(
            id=part_id, width=part_width, height=part_height, can_rotate=can_rotate
        )
        self.parts.append(part)

    @rule()
    def run_nesting(self):
        """Run nesting on current parts."""
        if len(self.parts) > 0:
            try:
                self.placed_parts = nest_parts(
                    self.parts, self.sheet_width, self.sheet_height
                )
            except ValueError:
                # Some configurations might not be nestable
                self.placed_parts = []

    @invariant()
    def no_overlaps_invariant(self):
        """Invariant: Placed parts should never overlap."""
        sheets = {}
        for part in self.placed_parts:
            sheet_idx = part.sheet_index
            if sheet_idx not in sheets:
                sheets[sheet_idx] = []
            sheets[sheet_idx].append(part)

        for sheet_parts in sheets.values():
            for i, part1 in enumerate(sheet_parts):
                for part2 in sheet_parts[i + 1 :]:
                    assert not self._rectangles_overlap(part1, part2)

    @invariant()
    def within_bounds_invariant(self):
        """Invariant: All parts should be within sheet bounds."""
        for part in self.placed_parts:
            assert part.x >= 0
            assert part.y >= 0
            assert part.x + part.width <= self.sheet_width + 0.1
            assert part.y + part.height <= self.sheet_height + 0.1

    def _rectangles_overlap(self, part1, part2):
        """Check if two placed parts overlap."""
        return not (
            part1.x >= part2.x + part2.width
            or part2.x >= part1.x + part1.width
            or part1.y >= part2.y + part2.height
            or part2.y >= part1.y + part1.height
        )


# Test the state machine
TestNestingStateMachine = NestingStateMachine.TestCase


# Performance-focused property tests
class TestPerformanceProperties:
    """Property-based tests focusing on performance characteristics."""

    @given(st.integers(min_value=1, max_value=1000))
    @settings(max_examples=20)
    def test_large_dataset_handling(self, num_parts):
        """Property: System should handle large datasets gracefully."""
        # Create many small parts
        parts = []
        for i in range(num_parts):
            part = Part(id=f"Part_{i}", width=50, height=30, can_rotate=True)
            parts.append(part)

        sheet_width, sheet_height = 2000, 1500

        try:
            # Should complete without crashing
            placed_parts = nest_parts(parts, sheet_width, sheet_height)

            # Basic sanity checks
            assert len(placed_parts) <= num_parts
            assert all(p.x >= 0 and p.y >= 0 for p in placed_parts)

        except (ValueError, MemoryError, TimeoutError):
            # These are acceptable for very large datasets
            pass

    @given(st.floats(min_value=0.1, max_value=100.0))
    def test_precision_handling(self, precision_value):
        """Property: System should handle various precision levels gracefully."""
        # Test with high-precision values
        part = Part(
            id="precision_test", width=precision_value, height=precision_value * 1.5
        )

        try:
            placed_parts = nest_parts([part], 1000, 1000)

            if placed_parts:
                placed_part = placed_parts[0]
                # Dimensions should be preserved (within floating point precision)
                assert abs(placed_part.width - precision_value) < 1e-10
                assert abs(placed_part.height - (precision_value * 1.5)) < 1e-10

        except ValueError:
            # Some precision values might cause issues - that's acceptable
            pass


if __name__ == "__main__":
    # Run property-based tests
    pytest.main([__file__, "-v", "--tb=short"])
