"""Smart cut sequence planning for optimized cutting operations."""

from dataclasses import dataclass
from enum import Enum

from SquatchCut.core import logger
from SquatchCut.core.nesting import PlacedPart


class CutDirection(Enum):
    """Direction of a cut operation."""

    HORIZONTAL = "horizontal"  # Left to right
    VERTICAL = "vertical"  # Bottom to top


class CutType(Enum):
    """Type of cut operation."""

    RIP = "rip"  # Cut along the grain (typically vertical)
    CROSSCUT = "crosscut"  # Cut across the grain (typically horizontal)
    TRIM = "trim"  # Final sizing cut


@dataclass
class CutOperation:
    """Represents a single cut operation."""

    cut_id: str
    cut_type: CutType
    direction: CutDirection
    position: float  # Position along the perpendicular axis
    start: float  # Start position along the cut axis
    end: float  # End position along the cut axis
    depth: float  # Cut depth (sheet thickness)
    parts_released: list[str]  # Part IDs released by this cut
    parts_affected: list[str]  # Part IDs that are cut through
    priority: int = 0  # Lower numbers = higher priority
    notes: str = ""


@dataclass
class CutSequence:
    """Complete cutting sequence for a sheet."""

    sheet_index: int
    sheet_width: float
    sheet_height: float
    operations: list[CutOperation]
    total_cut_length: float = 0.0
    estimated_time_minutes: float = 0.0


class CutSequencePlanner:
    """Plans optimal cutting sequences for nested layouts."""

    def __init__(
        self,
        kerf_width: float = 3.0,
        cut_speed_mm_per_min: float = 1000.0,
        setup_time_per_cut: float = 0.5,
    ):
        self.kerf_width = kerf_width
        self.cut_speed = cut_speed_mm_per_min
        self.setup_time = setup_time_per_cut

    def plan_cutting_sequence(
        self, placed_parts: list[PlacedPart], sheet_sizes: list[tuple[float, float]]
    ) -> list[CutSequence]:
        """Plan cutting sequences for all sheets."""
        sequences: list[CutSequence] = []

        # Group parts by sheet
        parts_by_sheet: dict[int, list[PlacedPart]] = {}
        for part in placed_parts:
            sheet_idx = part.sheet_index
            if sheet_idx not in parts_by_sheet:
                parts_by_sheet[sheet_idx] = []
            parts_by_sheet[sheet_idx].append(part)

        # Plan sequence for each sheet
        for sheet_idx, parts in parts_by_sheet.items():
            if sheet_idx < len(sheet_sizes):
                sheet_width, sheet_height = sheet_sizes[sheet_idx]
            else:
                sheet_width, sheet_height = (
                    sheet_sizes[-1] if sheet_sizes else (1220, 2440)
                )

            sequence = self._plan_sheet_sequence(
                parts, sheet_width, sheet_height, sheet_idx
            )
            sequences.append(sequence)

        return sequences

    def _plan_sheet_sequence(
        self,
        parts: list[PlacedPart],
        sheet_width: float,
        sheet_height: float,
        sheet_index: int,
    ) -> CutSequence:
        """Plan cutting sequence for a single sheet."""
        operations = []

        # Strategy: Rip cuts first (vertical), then crosscuts (horizontal)
        # This follows typical woodworking practice

        # 1. Collect all cut lines
        vertical_cuts = self._collect_vertical_cuts(parts, sheet_width, sheet_height)
        horizontal_cuts = self._collect_horizontal_cuts(
            parts, sheet_width, sheet_height
        )

        # 2. Plan rip cuts (vertical cuts from left to right)
        rip_operations = self._plan_rip_cuts(vertical_cuts, parts, sheet_height)
        operations.extend(rip_operations)

        # 3. Plan crosscuts (horizontal cuts from bottom to top)
        crosscut_operations = self._plan_crosscuts(horizontal_cuts, parts, sheet_width)
        operations.extend(crosscut_operations)

        # 4. Calculate total cut length and time
        total_length = sum(op.end - op.start for op in operations)
        estimated_time = (total_length / self.cut_speed) + (
            len(operations) * self.setup_time
        )

        return CutSequence(
            sheet_index=sheet_index,
            sheet_width=sheet_width,
            sheet_height=sheet_height,
            operations=operations,
            total_cut_length=total_length,
            estimated_time_minutes=estimated_time,
        )

    def _collect_vertical_cuts(
        self, parts: list[PlacedPart], sheet_width: float, sheet_height: float
    ) -> list[float]:
        """Collect all vertical cut positions."""
        cuts = set()

        for part in parts:
            # Left edge of part
            if part.x > 0:
                cuts.add(part.x)
            # Right edge of part
            if part.x + part.width < sheet_width:
                cuts.add(part.x + part.width)

        return sorted(cuts)

    def _collect_horizontal_cuts(
        self, parts: list[PlacedPart], sheet_width: float, sheet_height: float
    ) -> list[float]:
        """Collect all horizontal cut positions."""
        cuts = set()

        for part in parts:
            # Bottom edge of part
            if part.y > 0:
                cuts.add(part.y)
            # Top edge of part
            if part.y + part.height < sheet_height:
                cuts.add(part.y + part.height)

        return sorted(cuts)

    def _plan_rip_cuts(
        self, cut_positions: list[float], parts: list[PlacedPart], sheet_height: float
    ) -> list[CutOperation]:
        """Plan vertical rip cuts."""
        operations = []

        for i, position in enumerate(cut_positions):
            # Find parts affected by this cut
            parts_released = []
            parts_affected = []

            for part in parts:
                # Check if cut releases this part (cut is at right edge)
                if abs(part.x + part.width - position) < 0.1:
                    parts_released.append(part.id)
                # Check if cut goes through this part
                elif part.x < position < part.x + part.width:
                    parts_affected.append(part.id)

            # Determine cut extent
            start_y = 0.0
            end_y = sheet_height

            # Optimize cut length by finding actual extent needed
            min_y = min(
                (part.y for part in parts if part.x <= position <= part.x + part.width),
                default=0.0,
            )
            max_y = max(
                (
                    part.y + part.height
                    for part in parts
                    if part.x <= position <= part.x + part.width
                ),
                default=sheet_height,
            )

            if min_y > 0:
                start_y = min_y
            if max_y < sheet_height:
                end_y = max_y

            operation = CutOperation(
                cut_id=f"RIP_{i+1:02d}",
                cut_type=CutType.RIP,
                direction=CutDirection.VERTICAL,
                position=position,
                start=start_y,
                end=end_y,
                depth=18.0,  # Typical plywood thickness
                parts_released=parts_released,
                parts_affected=parts_affected,
                priority=i,
                notes=f"Rip cut at {position:.1f}mm from left edge",
            )
            operations.append(operation)

        return operations

    def _plan_crosscuts(
        self, cut_positions: list[float], parts: list[PlacedPart], sheet_width: float
    ) -> list[CutOperation]:
        """Plan horizontal crosscuts."""
        operations = []

        for i, position in enumerate(cut_positions):
            # Find parts affected by this cut
            parts_released = []
            parts_affected = []

            for part in parts:
                # Check if cut releases this part (cut is at top edge)
                if abs(part.y + part.height - position) < 0.1:
                    parts_released.append(part.id)
                # Check if cut goes through this part
                elif part.y < position < part.y + part.height:
                    parts_affected.append(part.id)

            # Determine cut extent
            start_x = 0.0
            end_x = sheet_width

            # Optimize cut length by finding actual extent needed
            min_x = min(
                (
                    part.x
                    for part in parts
                    if part.y <= position <= part.y + part.height
                ),
                default=0.0,
            )
            max_x = max(
                (
                    part.x + part.width
                    for part in parts
                    if part.y <= position <= part.y + part.height
                ),
                default=sheet_width,
            )

            if min_x > 0:
                start_x = min_x
            if max_x < sheet_width:
                end_x = max_x

            operation = CutOperation(
                cut_id=f"CROSS_{i+1:02d}",
                cut_type=CutType.CROSSCUT,
                direction=CutDirection.HORIZONTAL,
                position=position,
                start=start_x,
                end=end_x,
                depth=18.0,  # Typical plywood thickness
                parts_released=parts_released,
                parts_affected=parts_affected,
                priority=len(cut_positions) + i,  # After all rip cuts
                notes=f"Crosscut at {position:.1f}mm from bottom edge",
            )
            operations.append(operation)

        return operations

    def optimize_sequence(self, sequence: CutSequence) -> CutSequence:
        """Optimize cutting sequence to minimize material handling."""
        # Sort operations by priority and position
        optimized_ops = sorted(
            sequence.operations, key=lambda op: (op.priority, op.position)
        )

        # Apply optimization rules
        optimized_ops = self._minimize_offcut_handling(optimized_ops)
        optimized_ops = self._group_similar_cuts(optimized_ops)

        # Recalculate metrics
        total_length = sum(op.end - op.start for op in optimized_ops)
        estimated_time = (total_length / self.cut_speed) + (
            len(optimized_ops) * self.setup_time
        )

        return CutSequence(
            sheet_index=sequence.sheet_index,
            sheet_width=sequence.sheet_width,
            sheet_height=sequence.sheet_height,
            operations=optimized_ops,
            total_cut_length=total_length,
            estimated_time_minutes=estimated_time,
        )

    def _minimize_offcut_handling(
        self, operations: list[CutOperation]
    ) -> list[CutOperation]:
        """Reorder cuts to minimize handling of offcuts."""
        # Strategy: Complete all cuts that release parts before moving to next area
        rip_cuts = [op for op in operations if op.cut_type == CutType.RIP]
        crosscuts = [op for op in operations if op.cut_type == CutType.CROSSCUT]

        # Sort rip cuts by position (left to right)
        rip_cuts.sort(key=lambda op: op.position)

        # Sort crosscuts by position (bottom to top)
        crosscuts.sort(key=lambda op: op.position)

        return rip_cuts + crosscuts

    def _group_similar_cuts(self, operations: list[CutOperation]) -> list[CutOperation]:
        """Group similar cuts together to minimize setup changes."""
        # Already grouped by type in _minimize_offcut_handling
        return operations

    def generate_cut_report(self, sequences: list[CutSequence]) -> dict:
        """Generate a comprehensive cutting report."""
        total_cuts = sum(len(seq.operations) for seq in sequences)
        total_length = sum(seq.total_cut_length for seq in sequences)
        total_time = sum(seq.estimated_time_minutes for seq in sequences)

        # Analyze cut types
        rip_count = sum(
            len([op for op in seq.operations if op.cut_type == CutType.RIP])
            for seq in sequences
        )
        crosscut_count = sum(
            len([op for op in seq.operations if op.cut_type == CutType.CROSSCUT])
            for seq in sequences
        )

        return {
            "summary": {
                "total_sheets": len(sequences),
                "total_cuts": total_cuts,
                "total_cut_length_mm": total_length,
                "estimated_time_minutes": total_time,
                "rip_cuts": rip_count,
                "crosscuts": crosscut_count,
            },
            "sequences": sequences,
            "efficiency_metrics": {
                "avg_cuts_per_sheet": total_cuts / len(sequences) if sequences else 0,
                "avg_cut_length_mm": total_length / total_cuts if total_cuts else 0,
                "cut_speed_mm_per_min": self.cut_speed,
                "setup_time_per_cut_min": self.setup_time,
            },
        }


def plan_optimal_cutting_sequence(
    placed_parts: list[PlacedPart],
    sheet_sizes: list[tuple[float, float]],
    kerf_width: float = 3.0,
) -> list[CutSequence]:
    """High-level function to plan optimal cutting sequences."""
    planner = CutSequencePlanner(kerf_width=kerf_width)
    sequences = planner.plan_cutting_sequence(placed_parts, sheet_sizes)

    # Optimize each sequence
    optimized_sequences = []
    for sequence in sequences:
        optimized = planner.optimize_sequence(sequence)
        optimized_sequences.append(optimized)

    logger.info(f"Planned cutting sequences for {len(optimized_sequences)} sheets")
    return optimized_sequences
