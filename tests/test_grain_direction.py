"""Tests for grain direction support in nesting."""


from SquatchCut.core.grain_direction import (
    GrainAwarePart,
    GrainConstraints,
    GrainDirection,
    add_grain_info_to_parts,
    calculate_grain_penalty,
    create_grain_report,
    infer_grain_direction_from_dimensions,
    is_grain_compatible,
    optimize_rotation_for_grain,
    parse_grain_direction,
    validate_grain_constraints,
)
from SquatchCut.core.nesting import Part, PlacedPart


class TestGrainDirection:
    """Test grain direction enumeration."""

    def test_grain_direction_values(self):
        """Test grain direction enum values."""
        assert GrainDirection.HORIZONTAL.value == "horizontal"
        assert GrainDirection.VERTICAL.value == "vertical"
        assert GrainDirection.ANY.value == "any"


class TestGrainConstraints:
    """Test grain constraints configuration."""

    def test_default_constraints(self):
        """Test default grain constraints."""
        constraints = GrainConstraints()
        assert constraints.sheet_grain == GrainDirection.HORIZONTAL
        assert constraints.enforce_part_grain is True
        assert constraints.allow_cross_grain is False
        assert constraints.grain_penalty_factor == 0.1

    def test_custom_constraints(self):
        """Test custom grain constraints."""
        constraints = GrainConstraints(
            sheet_grain=GrainDirection.VERTICAL,
            enforce_part_grain=False,
            allow_cross_grain=True,
            grain_penalty_factor=0.2,
        )
        assert constraints.sheet_grain == GrainDirection.VERTICAL
        assert constraints.enforce_part_grain is False
        assert constraints.allow_cross_grain is True
        assert constraints.grain_penalty_factor == 0.2


class TestGrainAwarePart:
    """Test grain-aware part implementation."""

    def test_grain_aware_part_creation(self):
        """Test creating a grain-aware part."""
        part = GrainAwarePart(
            id="test_part",
            width=100,
            height=50,
            can_rotate=True,
            grain_direction=GrainDirection.HORIZONTAL,
        )

        assert part.id == "test_part"
        assert part.width == 100
        assert part.height == 50
        assert part.can_rotate is True
        assert part.grain_direction == GrainDirection.HORIZONTAL

    def test_from_part_conversion(self):
        """Test converting regular part to grain-aware part."""
        regular_part = Part(id="regular", width=80, height=60, can_rotate=False)

        grain_part = GrainAwarePart.from_part(
            regular_part, grain_direction=GrainDirection.VERTICAL
        )

        assert grain_part.id == "regular"
        assert grain_part.width == 80
        assert grain_part.height == 60
        assert grain_part.can_rotate is False
        assert grain_part.grain_direction == GrainDirection.VERTICAL

    def test_from_part_default_grain(self):
        """Test converting part with default grain direction."""
        regular_part = Part(id="test", width=100, height=50)
        grain_part = GrainAwarePart.from_part(regular_part)

        assert grain_part.grain_direction == GrainDirection.ANY


class TestGrainInference:
    """Test grain direction inference from dimensions."""

    def test_infer_horizontal_grain(self):
        """Test inferring horizontal grain from wide parts."""
        # Wide part should suggest horizontal grain
        grain = infer_grain_direction_from_dimensions(200, 50)
        assert grain == GrainDirection.HORIZONTAL

    def test_infer_vertical_grain(self):
        """Test inferring vertical grain from tall parts."""
        # Tall part should suggest vertical grain
        grain = infer_grain_direction_from_dimensions(50, 200)
        assert grain == GrainDirection.VERTICAL

    def test_infer_any_grain(self):
        """Test inferring no preference for square-ish parts."""
        # Square part should have no preference
        grain = infer_grain_direction_from_dimensions(100, 100)
        assert grain == GrainDirection.ANY

        # Slightly rectangular but not extreme
        grain = infection_from_dimensions(120, 100)
        assert grain == GrainDirection.ANY

    def test_infer_edge_cases(self):
        """Test edge cases for grain inference."""
        # Zero dimensions
        grain = infer_grain_direction_from_dimensions(0, 100)
        assert grain == GrainDirection.VERTICAL

        grain = infer_grain_direction_from_dimensions(100, 0)
        assert grain == GrainDirection.ANY  # Avoid division by zero


class TestGrainParsing:
    """Test parsing grain direction from strings."""

    def test_parse_horizontal_variants(self):
        """Test parsing horizontal grain variants."""
        variants = ["h", "horizontal", "horiz", "left-right", "lr", "H", "HORIZONTAL"]

        for variant in variants:
            grain = parse_grain_direction(variant)
            assert grain == GrainDirection.HORIZONTAL

    def test_parse_vertical_variants(self):
        """Test parsing vertical grain variants."""
        variants = ["v", "vertical", "vert", "up-down", "ud", "V", "VERTICAL"]

        for variant in variants:
            grain = parse_grain_direction(variant)
            assert grain == GrainDirection.VERTICAL

    def test_parse_any_variants(self):
        """Test parsing 'any' grain variants."""
        variants = ["", "any", "none", "unknown", "random", None]

        for variant in variants:
            grain = parse_grain_direction(variant)
            assert grain == GrainDirection.ANY


class TestGrainCompatibility:
    """Test grain compatibility checking."""

    def setup_method(self):
        """Set up test fixtures."""
        self.constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL,
            enforce_part_grain=True,
            allow_cross_grain=False,
        )

    def test_compatible_grain_no_rotation(self):
        """Test compatible grain without rotation."""
        part = GrainAwarePart(
            "test", 100, 50, grain_direction=GrainDirection.HORIZONTAL
        )

        compatible = is_grain_compatible(
            part, 0, GrainDirection.HORIZONTAL, self.constraints
        )
        assert compatible is True

    def test_compatible_grain_with_rotation(self):
        """Test compatible grain with rotation."""
        part = GrainAwarePart("test", 100, 50, grain_direction=GrainDirection.VERTICAL)

        # Vertical part rotated 90° should match horizontal sheet
        compatible = is_grain_compatible(
            part, 90, GrainDirection.HORIZONTAL, self.constraints
        )
        assert compatible is True

    def test_incompatible_grain(self):
        """Test incompatible grain direction."""
        part = GrainAwarePart("test", 100, 50, grain_direction=GrainDirection.VERTICAL)

        # Vertical part on horizontal sheet without rotation
        compatible = is_grain_compatible(
            part, 0, GrainDirection.HORIZONTAL, self.constraints
        )
        assert compatible is False

    def test_any_grain_always_compatible(self):
        """Test that 'any' grain is always compatible."""
        part = GrainAwarePart("test", 100, 50, grain_direction=GrainDirection.ANY)

        compatible = is_grain_compatible(
            part, 0, GrainDirection.HORIZONTAL, self.constraints
        )
        assert compatible is True

        compatible = is_grain_compatible(
            part, 90, GrainDirection.VERTICAL, self.constraints
        )
        assert compatible is True

    def test_cross_grain_allowed(self):
        """Test compatibility when cross-grain is allowed."""
        constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL, allow_cross_grain=True
        )

        part = GrainAwarePart("test", 100, 50, grain_direction=GrainDirection.VERTICAL)

        # Should be compatible even though grain doesn't match
        compatible = is_grain_compatible(
            part, 0, GrainDirection.HORIZONTAL, constraints
        )
        assert compatible is True

    def test_enforcement_disabled(self):
        """Test compatibility when enforcement is disabled."""
        constraints = GrainConstraints(enforce_part_grain=False)

        part = GrainAwarePart("test", 100, 50, grain_direction=GrainDirection.VERTICAL)

        # Should always be compatible when enforcement is off
        compatible = is_grain_compatible(
            part, 0, GrainDirection.HORIZONTAL, constraints
        )
        assert compatible is True


class TestGrainPenalty:
    """Test grain penalty calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.constraints = GrainConstraints(
            grain_penalty_factor=0.2, allow_cross_grain=True
        )

    def test_no_penalty_for_compatible(self):
        """Test no penalty for compatible grain."""
        part = GrainAwarePart(
            "test", 100, 50, grain_direction=GrainDirection.HORIZONTAL
        )

        penalty = calculate_grain_penalty(
            part, 0, GrainDirection.HORIZONTAL, self.constraints
        )
        assert penalty == 0.0

    def test_penalty_for_incompatible(self):
        """Test penalty for incompatible grain."""
        constraints = GrainConstraints(
            grain_penalty_factor=0.2, allow_cross_grain=False
        )

        part = GrainAwarePart("test", 100, 50, grain_direction=GrainDirection.VERTICAL)

        penalty = calculate_grain_penalty(
            part, 0, GrainDirection.HORIZONTAL, constraints
        )
        assert penalty == 0.2

    def test_no_penalty_when_enforcement_disabled(self):
        """Test no penalty when enforcement is disabled."""
        constraints = GrainConstraints(enforce_part_grain=False)

        part = GrainAwarePart("test", 100, 50, grain_direction=GrainDirection.VERTICAL)

        penalty = calculate_grain_penalty(
            part, 0, GrainDirection.HORIZONTAL, constraints
        )
        assert penalty == 0.0


class TestRotationOptimization:
    """Test rotation optimization for grain direction."""

    def setup_method(self):
        """Set up test fixtures."""
        self.constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL,
            enforce_part_grain=True,
            allow_cross_grain=False,
        )

    def test_optimize_rotation_compatible(self):
        """Test rotation optimization for compatible part."""
        part = GrainAwarePart(
            "test", 100, 50, can_rotate=True, grain_direction=GrainDirection.HORIZONTAL
        )

        rotations = optimize_rotation_for_grain(
            part, GrainDirection.HORIZONTAL, self.constraints
        )

        # Should prefer 0° rotation
        assert 0 in rotations
        assert len(rotations) >= 1

    def test_optimize_rotation_needs_rotation(self):
        """Test rotation optimization when rotation is needed."""
        part = GrainAwarePart(
            "test", 100, 50, can_rotate=True, grain_direction=GrainDirection.VERTICAL
        )

        rotations = optimize_rotation_for_grain(
            part, GrainDirection.HORIZONTAL, self.constraints
        )

        # Should prefer 90° rotation to align vertical grain with horizontal sheet
        assert 90 in rotations

    def test_optimize_rotation_cannot_rotate(self):
        """Test rotation optimization when part cannot rotate."""
        part = GrainAwarePart(
            "test", 100, 50, can_rotate=False, grain_direction=GrainDirection.VERTICAL
        )

        rotations = optimize_rotation_for_grain(
            part, GrainDirection.HORIZONTAL, self.constraints
        )

        # Should return empty list since part can't rotate and isn't compatible
        assert len(rotations) == 0

    def test_optimize_rotation_cross_grain_allowed(self):
        """Test rotation optimization when cross-grain is allowed."""
        constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL, allow_cross_grain=True
        )

        part = GrainAwarePart(
            "test", 100, 50, can_rotate=True, grain_direction=GrainDirection.VERTICAL
        )

        rotations = optimize_rotation_for_grain(
            part, GrainDirection.HORIZONTAL, constraints
        )

        # Should return both rotations since cross-grain is allowed
        assert 0 in rotations
        assert 90 in rotations


class TestGrainInfoAddition:
    """Test adding grain information to parts."""

    def test_add_grain_info_with_data(self):
        """Test adding grain info with provided data."""
        parts = [Part(id="A", width=100, height=50), Part(id="B", width=60, height=120)]

        grain_data = {
            "A": {"grain_direction": "horizontal"},
            "B": {"grain_direction": "vertical"},
        }

        grain_parts = add_grain_info_to_parts(parts, grain_data)

        assert len(grain_parts) == 2
        assert grain_parts[0].grain_direction == GrainDirection.HORIZONTAL
        assert grain_parts[1].grain_direction == GrainDirection.VERTICAL

    def test_add_grain_info_inferred(self):
        """Test adding grain info with inference."""
        parts = [
            Part(id="A", width=200, height=50),  # Should infer horizontal
            Part(id="B", width=50, height=200),  # Should infer vertical
        ]

        grain_parts = add_grain_info_to_parts(parts)

        assert len(grain_parts) == 2
        assert grain_parts[0].grain_direction == GrainDirection.HORIZONTAL
        assert grain_parts[1].grain_direction == GrainDirection.VERTICAL

    def test_add_grain_info_mixed(self):
        """Test adding grain info with mixed data and inference."""
        parts = [Part(id="A", width=100, height=50), Part(id="B", width=200, height=60)]

        grain_data = {
            "A": {"grain_direction": "vertical"}
            # B will be inferred
        }

        grain_parts = add_grain_info_to_parts(parts, grain_data)

        assert grain_parts[0].grain_direction == GrainDirection.VERTICAL  # From data
        assert grain_parts[1].grain_direction == GrainDirection.HORIZONTAL  # Inferred


class TestGrainValidation:
    """Test grain constraint validation."""

    def test_validate_compatible_parts(self):
        """Test validation with compatible parts."""
        parts = [
            GrainAwarePart(
                "A", 100, 50, can_rotate=True, grain_direction=GrainDirection.HORIZONTAL
            ),
            GrainAwarePart(
                "B", 80, 60, can_rotate=True, grain_direction=GrainDirection.VERTICAL
            ),
        ]

        constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL, allow_cross_grain=True
        )

        warnings = validate_grain_constraints(parts, constraints)
        assert len(warnings) == 0

    def test_validate_incompatible_parts(self):
        """Test validation with incompatible parts."""
        parts = [
            GrainAwarePart(
                "A", 100, 50, can_rotate=False, grain_direction=GrainDirection.VERTICAL
            )
        ]

        constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL, allow_cross_grain=False
        )

        warnings = validate_grain_constraints(parts, constraints)
        assert len(warnings) > 0
        assert "A" in warnings[0]

    def test_validate_enforcement_disabled(self):
        """Test validation when enforcement is disabled."""
        parts = [
            GrainAwarePart(
                "A", 100, 50, can_rotate=False, grain_direction=GrainDirection.VERTICAL
            )
        ]

        constraints = GrainConstraints(enforce_part_grain=False)

        warnings = validate_grain_constraints(parts, constraints)
        assert len(warnings) == 0


class TestGrainReport:
    """Test grain direction reporting."""

    def test_create_grain_report_enforcement_disabled(self):
        """Test grain report when enforcement is disabled."""
        placed_parts = []
        parts = []
        constraints = GrainConstraints(enforce_part_grain=False)

        report = create_grain_report(placed_parts, parts, constraints)

        assert report["grain_enforcement"] is False
        assert "message" in report

    def test_create_grain_report_with_parts(self):
        """Test grain report with actual parts."""
        parts = [
            GrainAwarePart("A", 100, 50, grain_direction=GrainDirection.HORIZONTAL),
            GrainAwarePart("B", 80, 60, grain_direction=GrainDirection.VERTICAL),
        ]

        placed_parts = [
            PlacedPart(
                id="A", x=0, y=0, width=100, height=50, rotation_deg=0, sheet_index=0
            ),
            PlacedPart(
                id="B", x=100, y=0, width=60, height=80, rotation_deg=90, sheet_index=0
            ),
        ]

        constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL, enforce_part_grain=True
        )

        report = create_grain_report(placed_parts, parts, constraints)

        assert report["grain_enforcement"] is True
        assert report["total_parts"] == 2
        assert report["sheet_grain"] == "horizontal"
        assert "compatibility_rate" in report
        assert "part_details" in report
        assert len(report["part_details"]) == 2

    def test_grain_report_compatibility_calculation(self):
        """Test compatibility rate calculation in grain report."""
        parts = [
            GrainAwarePart("A", 100, 50, grain_direction=GrainDirection.HORIZONTAL),
            GrainAwarePart("B", 80, 60, grain_direction=GrainDirection.VERTICAL),
        ]

        placed_parts = [
            PlacedPart(
                id="A", x=0, y=0, width=100, height=50, rotation_deg=0, sheet_index=0
            ),  # Compatible
            PlacedPart(
                id="B", x=100, y=0, width=80, height=60, rotation_deg=0, sheet_index=0
            ),  # Not compatible
        ]

        constraints = GrainConstraints(
            sheet_grain=GrainDirection.HORIZONTAL, allow_cross_grain=False
        )

        report = create_grain_report(placed_parts, parts, constraints)

        # Should have 50% compatibility (1 out of 2 parts compatible)
        assert report["compatible_parts"] == 1
        assert report["cross_grain_parts"] == 1
        assert report["compatibility_rate"] == 0.5
