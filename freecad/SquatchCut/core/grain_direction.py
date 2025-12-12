"""Grain direction support for wood nesting optimization."""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from SquatchCut.core.nesting import Part, PlacedPart


class GrainDirection(Enum):
    """Wood grain direction options."""

    HORIZONTAL = "horizontal"  # Grain runs left-right
    VERTICAL = "vertical"  # Grain runs up-down
    ANY = "any"  # No grain preference


@dataclass
class GrainConstraints:
    """Grain direction constraints for nesting."""

    sheet_grain: GrainDirection = GrainDirection.HORIZONTAL
    enforce_part_grain: bool = True
    allow_cross_grain: bool = False  # Allow parts perpendicular to sheet grain
    grain_penalty_factor: float = 0.1  # Fitness penalty for cross-grain placement


class GrainAwarePart(Part):
    """Part with grain direction information."""

    def __init__(
        self,
        id: str,
        width: float,
        height: float,
        can_rotate: bool = False,
        grain_direction: GrainDirection = GrainDirection.ANY,
    ):
        super().__init__(id, width, height, can_rotate)
        self.grain_direction = grain_direction

    @classmethod
    def from_part(
        cls, part: Part, grain_direction: GrainDirection = GrainDirection.ANY
    ):
        """Create GrainAwarePart from regular Part."""
        return cls(
            id=part.id,
            width=part.width,
            height=part.height,
            can_rotate=getattr(part, "can_rotate", False),
            grain_direction=grain_direction,
        )


def infer_grain_direction_from_dimensions(
    width: float, height: float
) -> GrainDirection:
    """Infer likely grain direction from part dimensions."""
    aspect_ratio = width / height if height > 0 else 1.0

    # If significantly wider than tall, grain likely runs horizontally
    if aspect_ratio > 2.0:
        return GrainDirection.HORIZONTAL
    # If significantly taller than wide, grain likely runs vertically
    elif aspect_ratio < 0.5:
        return GrainDirection.VERTICAL
    else:
        # Square-ish parts, no clear preference
        return GrainDirection.ANY


def parse_grain_direction(grain_str: str) -> GrainDirection:
    """Parse grain direction from string (for CSV import)."""
    if not grain_str:
        return GrainDirection.ANY

    grain_str = grain_str.lower().strip()

    if grain_str in ["h", "horizontal", "horiz", "left-right", "lr"]:
        return GrainDirection.HORIZONTAL
    elif grain_str in ["v", "vertical", "vert", "up-down", "ud"]:
        return GrainDirection.VERTICAL
    else:
        return GrainDirection.ANY


def is_grain_compatible(
    part: GrainAwarePart,
    placement_rotation: int,
    sheet_grain: GrainDirection,
    constraints: GrainConstraints,
) -> bool:
    """Check if part placement is compatible with grain constraints."""
    if not constraints.enforce_part_grain:
        return True

    if part.grain_direction == GrainDirection.ANY:
        return True

    if sheet_grain == GrainDirection.ANY:
        return True

    # Determine part's effective grain direction after rotation
    if placement_rotation == 90 or placement_rotation == 270:
        # Part is rotated, so grain direction flips
        if part.grain_direction == GrainDirection.HORIZONTAL:
            effective_grain = GrainDirection.VERTICAL
        elif part.grain_direction == GrainDirection.VERTICAL:
            effective_grain = GrainDirection.HORIZONTAL
        else:
            effective_grain = GrainDirection.ANY
    else:
        effective_grain = part.grain_direction

    # Check compatibility
    if effective_grain == sheet_grain:
        return True  # Perfect match
    elif constraints.allow_cross_grain:
        return True  # Cross-grain allowed
    else:
        return False  # Cross-grain not allowed


def calculate_grain_penalty(
    part: GrainAwarePart,
    placement_rotation: int,
    sheet_grain: GrainDirection,
    constraints: GrainConstraints,
) -> float:
    """Calculate fitness penalty for grain direction mismatch."""
    if not constraints.enforce_part_grain:
        return 0.0

    if is_grain_compatible(part, placement_rotation, sheet_grain, constraints):
        return 0.0
    else:
        return constraints.grain_penalty_factor


def optimize_rotation_for_grain(
    part: GrainAwarePart, sheet_grain: GrainDirection, constraints: GrainConstraints
) -> list[int]:
    """Get preferred rotation angles for part considering grain direction."""
    if not constraints.enforce_part_grain or part.grain_direction == GrainDirection.ANY:
        # No grain constraints, return all possible rotations
        return [0, 90] if getattr(part, "can_rotate", False) else [0]

    preferred_rotations = []
    possible_rotations = [0, 90] if getattr(part, "can_rotate", False) else [0]

    for rotation in possible_rotations:
        if is_grain_compatible(part, rotation, sheet_grain, constraints):
            preferred_rotations.append(rotation)

    # If no compatible rotations and cross-grain is allowed, return all
    if not preferred_rotations and constraints.allow_cross_grain:
        preferred_rotations = possible_rotations

    return preferred_rotations or [0]  # Always return at least one rotation


def add_grain_info_to_parts(
    parts: list[Part], grain_data: dict[str, Any] | None = None
) -> list[GrainAwarePart]:
    """Convert regular parts to grain-aware parts."""
    grain_aware_parts = []

    for part in parts:
        # Try to get grain direction from provided data
        grain_direction = GrainDirection.ANY

        if grain_data and part.id in grain_data:
            grain_str = grain_data[part.id].get("grain_direction", "")
            grain_direction = parse_grain_direction(grain_str)

        # If no explicit grain direction, try to infer from dimensions
        if grain_direction == GrainDirection.ANY:
            grain_direction = infer_grain_direction_from_dimensions(
                part.width, part.height
            )

        grain_aware_part = GrainAwarePart.from_part(part, grain_direction)
        grain_aware_parts.append(grain_aware_part)

    return grain_aware_parts


def validate_grain_constraints(
    parts: list[GrainAwarePart], constraints: GrainConstraints
) -> list[str]:
    """Validate that parts can be placed with given grain constraints."""
    warnings = []

    if not constraints.enforce_part_grain:
        return warnings

    incompatible_parts = []

    for part in parts:
        if part.grain_direction == GrainDirection.ANY:
            continue

        preferred_rotations = optimize_rotation_for_grain(
            part, constraints.sheet_grain, constraints
        )

        if not preferred_rotations:
            incompatible_parts.append(part.id)

    if incompatible_parts:
        warnings.append(
            f"Parts with incompatible grain directions: {', '.join(incompatible_parts)}. "
            f"Consider enabling cross-grain placement or adjusting grain constraints."
        )

    return warnings


def create_grain_report(
    placed_parts: list[PlacedPart],
    parts: list[GrainAwarePart],
    constraints: GrainConstraints,
) -> dict[str, Any]:
    """Create a report on grain direction compliance."""
    if not constraints.enforce_part_grain:
        return {
            "grain_enforcement": False,
            "message": "Grain direction enforcement disabled",
        }

    # Create lookup for parts by ID
    parts_by_id = {part.id: part for part in parts}

    compatible_count = 0
    cross_grain_count = 0
    total_parts = len(placed_parts)

    part_details = []

    for pp in placed_parts:
        part = parts_by_id.get(pp.id)
        if not part:
            continue

        is_compatible = is_grain_compatible(
            part, pp.rotation_deg, constraints.sheet_grain, constraints
        )
        penalty = calculate_grain_penalty(
            part, pp.rotation_deg, constraints.sheet_grain, constraints
        )

        if is_compatible and penalty == 0:
            compatible_count += 1
            status = "compatible"
        else:
            cross_grain_count += 1
            status = "cross_grain"

        part_details.append(
            {
                "id": pp.id,
                "part_grain": part.grain_direction.value,
                "rotation": pp.rotation_deg,
                "status": status,
                "penalty": penalty,
            }
        )

    compatibility_rate = compatible_count / total_parts if total_parts > 0 else 0

    return {
        "grain_enforcement": True,
        "sheet_grain": constraints.sheet_grain.value,
        "total_parts": total_parts,
        "compatible_parts": compatible_count,
        "cross_grain_parts": cross_grain_count,
        "compatibility_rate": compatibility_rate,
        "allow_cross_grain": constraints.allow_cross_grain,
        "part_details": part_details,
    }
