"""Quality assurance and validation for nesting layouts."""

from dataclasses import dataclass
from enum import Enum

from SquatchCut.core import logger
from SquatchCut.core.nesting import PlacedPart


class QualityIssueType(Enum):
    """Types of quality issues that can be detected."""

    OVERLAP = "overlap"
    OUT_OF_BOUNDS = "out_of_bounds"
    INSUFFICIENT_SPACING = "insufficient_spacing"
    ROTATION_ERROR = "rotation_error"
    DIMENSION_MISMATCH = "dimension_mismatch"
    GRAIN_VIOLATION = "grain_violation"


class QualitySeverity(Enum):
    """Severity levels for quality issues."""

    CRITICAL = "critical"  # Must be fixed
    WARNING = "warning"  # Should be reviewed
    INFO = "info"  # Informational only


@dataclass
class QualityIssue:
    """Represents a quality issue found in the layout."""

    issue_type: QualityIssueType
    severity: QualitySeverity
    part_ids: list[str]
    sheet_index: int
    description: str
    suggested_fix: str = ""
    coordinates: tuple[float, float] | None = None
    affected_area: tuple[float, float, float, float] | None = (
        None  # x, y, width, height
    )


@dataclass
class QualityReport:
    """Comprehensive quality report for a nesting layout."""

    layout_id: str
    timestamp: str
    total_parts: int
    total_sheets: int
    issues: list[QualityIssue]
    metrics: dict[str, float]
    passed_checks: list[str]
    failed_checks: list[str]
    overall_score: float  # 0-100


class QualityAssuranceChecker:
    """Performs quality assurance checks on nesting layouts."""

    def __init__(
        self,
        min_spacing: float = 3.0,
        tolerance: float = 0.1,
        check_grain_direction: bool = False,
    ):
        self.min_spacing = min_spacing
        self.tolerance = tolerance
        self.check_grain_direction = check_grain_direction

    def check_layout_quality(
        self,
        placed_parts: list[PlacedPart],
        sheet_sizes: list[tuple[float, float]],
        original_parts: list | None = None,
    ) -> QualityReport:
        """Perform comprehensive quality checks on the layout."""
        import datetime

        issues = []
        passed_checks = []
        failed_checks = []

        # 1. Check for overlaps
        overlap_issues = self._check_overlaps(placed_parts)
        if overlap_issues:
            issues.extend(overlap_issues)
            failed_checks.append("overlap_detection")
        else:
            passed_checks.append("overlap_detection")

        # 2. Check bounds compliance
        bounds_issues = self._check_bounds_compliance(placed_parts, sheet_sizes)
        if bounds_issues:
            issues.extend(bounds_issues)
            failed_checks.append("bounds_compliance")
        else:
            passed_checks.append("bounds_compliance")

        # 3. Check spacing requirements
        spacing_issues = self._check_spacing_requirements(placed_parts)
        if spacing_issues:
            issues.extend(spacing_issues)
            failed_checks.append("spacing_requirements")
        else:
            passed_checks.append("spacing_requirements")

        # 4. Check rotation consistency
        rotation_issues = self._check_rotation_consistency(placed_parts)
        if rotation_issues:
            issues.extend(rotation_issues)
            failed_checks.append("rotation_consistency")
        else:
            passed_checks.append("rotation_consistency")

        # 5. Check dimension consistency (if original parts provided)
        if original_parts:
            dimension_issues = self._check_dimension_consistency(
                placed_parts, original_parts
            )
            if dimension_issues:
                issues.extend(dimension_issues)
                failed_checks.append("dimension_consistency")
            else:
                passed_checks.append("dimension_consistency")

        # 6. Check grain direction (if enabled)
        if self.check_grain_direction:
            grain_issues = self._check_grain_direction_compliance(placed_parts)
            if grain_issues:
                issues.extend(grain_issues)
                failed_checks.append("grain_direction")
            else:
                passed_checks.append("grain_direction")

        # Calculate metrics
        metrics = self._calculate_quality_metrics(placed_parts, sheet_sizes, issues)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            issues, len(passed_checks), len(failed_checks)
        )

        return QualityReport(
            layout_id=f"layout_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.datetime.now().isoformat(),
            total_parts=len(placed_parts),
            total_sheets=len(set(part.sheet_index for part in placed_parts)),
            issues=issues,
            metrics=metrics,
            passed_checks=passed_checks,
            failed_checks=failed_checks,
            overall_score=overall_score,
        )

    def _check_overlaps(self, placed_parts: list[PlacedPart]) -> list[QualityIssue]:
        """Check for overlapping parts."""
        issues = []

        for i, part1 in enumerate(placed_parts):
            for j, part2 in enumerate(placed_parts[i + 1 :], i + 1):
                # Only check parts on the same sheet
                if part1.sheet_index != part2.sheet_index:
                    continue

                # Check for overlap
                if self._rectangles_overlap(
                    (part1.x, part1.y, part1.width, part1.height),
                    (part2.x, part2.y, part2.width, part2.height),
                ):
                    overlap_area = self._calculate_overlap_area(
                        (part1.x, part1.y, part1.width, part1.height),
                        (part2.x, part2.y, part2.width, part2.height),
                    )

                    issues.append(
                        QualityIssue(
                            issue_type=QualityIssueType.OVERLAP,
                            severity=QualitySeverity.CRITICAL,
                            part_ids=[part1.id, part2.id],
                            sheet_index=part1.sheet_index,
                            description=f"Parts {part1.id} and {part2.id} overlap by {overlap_area:.1f} sq mm",
                            suggested_fix="Adjust part positions to eliminate overlap",
                            coordinates=(max(part1.x, part2.x), max(part1.y, part2.y)),
                            affected_area=self._get_overlap_bounds(
                                (part1.x, part1.y, part1.width, part1.height),
                                (part2.x, part2.y, part2.width, part2.height),
                            ),
                        )
                    )

        return issues

    def _check_bounds_compliance(
        self, placed_parts: list[PlacedPart], sheet_sizes: list[tuple[float, float]]
    ) -> list[QualityIssue]:
        """Check that all parts are within sheet boundaries."""
        issues = []

        for part in placed_parts:
            # Get sheet dimensions
            if part.sheet_index < len(sheet_sizes):
                sheet_width, sheet_height = sheet_sizes[part.sheet_index]
            else:
                sheet_width, sheet_height = (
                    sheet_sizes[-1] if sheet_sizes else (1220, 2440)
                )

            # Check if part exceeds sheet bounds
            if (
                part.x < 0
                or part.y < 0
                or part.x + part.width > sheet_width + self.tolerance
                or part.y + part.height > sheet_height + self.tolerance
            ):

                issues.append(
                    QualityIssue(
                        issue_type=QualityIssueType.OUT_OF_BOUNDS,
                        severity=QualitySeverity.CRITICAL,
                        part_ids=[part.id],
                        sheet_index=part.sheet_index,
                        description=f"Part {part.id} extends beyond sheet boundaries",
                        suggested_fix="Resize part or use larger sheet",
                        coordinates=(part.x, part.y),
                        affected_area=(part.x, part.y, part.width, part.height),
                    )
                )

        return issues

    def _check_spacing_requirements(
        self, placed_parts: list[PlacedPart]
    ) -> list[QualityIssue]:
        """Check minimum spacing between parts."""
        issues = []

        for i, part1 in enumerate(placed_parts):
            for j, part2 in enumerate(placed_parts[i + 1 :], i + 1):
                # Only check parts on the same sheet
                if part1.sheet_index != part2.sheet_index:
                    continue

                # Calculate minimum distance between parts
                min_distance = self._calculate_min_distance(
                    (part1.x, part1.y, part1.width, part1.height),
                    (part2.x, part2.y, part2.width, part2.height),
                )

                if min_distance < self.min_spacing - self.tolerance:
                    issues.append(
                        QualityIssue(
                            issue_type=QualityIssueType.INSUFFICIENT_SPACING,
                            severity=QualitySeverity.WARNING,
                            part_ids=[part1.id, part2.id],
                            sheet_index=part1.sheet_index,
                            description=f"Parts {part1.id} and {part2.id} have insufficient spacing ({min_distance:.1f}mm < {self.min_spacing}mm)",
                            suggested_fix=f"Increase spacing to at least {self.min_spacing}mm",
                            coordinates=(
                                (part1.x + part1.width / 2 + part2.x + part2.width / 2)
                                / 2,
                                (
                                    part1.y
                                    + part1.height / 2
                                    + part2.y
                                    + part2.height / 2
                                )
                                / 2,
                            ),
                        )
                    )

        return issues

    def _check_rotation_consistency(
        self, placed_parts: list[PlacedPart]
    ) -> list[QualityIssue]:
        """Check for invalid rotation angles."""
        issues = []

        valid_rotations = {0, 90, 180, 270}

        for part in placed_parts:
            if part.rotation_deg not in valid_rotations:
                issues.append(
                    QualityIssue(
                        issue_type=QualityIssueType.ROTATION_ERROR,
                        severity=QualitySeverity.WARNING,
                        part_ids=[part.id],
                        sheet_index=part.sheet_index,
                        description=f"Part {part.id} has invalid rotation angle: {part.rotation_deg}°",
                        suggested_fix="Use standard rotation angles (0°, 90°, 180°, 270°)",
                        coordinates=(part.x, part.y),
                    )
                )

        return issues

    def _check_dimension_consistency(
        self, placed_parts: list[PlacedPart], original_parts: list
    ) -> list[QualityIssue]:
        """Check that placed parts match original dimensions."""
        issues = []

        # Create lookup for original parts
        original_by_id = {
            getattr(part, "id", str(i)): part for i, part in enumerate(original_parts)
        }

        for placed_part in placed_parts:
            original = original_by_id.get(placed_part.id)
            if not original:
                continue

            orig_width = getattr(original, "width", 0)
            orig_height = getattr(original, "height", 0)

            # Account for rotation
            if placed_part.rotation_deg in [90, 270]:
                expected_width = orig_height
                expected_height = orig_width
            else:
                expected_width = orig_width
                expected_height = orig_height

            # Check dimensions with tolerance
            if (
                abs(placed_part.width - expected_width) > self.tolerance
                or abs(placed_part.height - expected_height) > self.tolerance
            ):

                issues.append(
                    QualityIssue(
                        issue_type=QualityIssueType.DIMENSION_MISMATCH,
                        severity=QualitySeverity.WARNING,
                        part_ids=[placed_part.id],
                        sheet_index=placed_part.sheet_index,
                        description=f"Part {placed_part.id} dimensions don't match original: "
                        f"expected {expected_width}x{expected_height}, "
                        f"got {placed_part.width}x{placed_part.height}",
                        suggested_fix="Verify part dimensions and rotation",
                        coordinates=(placed_part.x, placed_part.y),
                    )
                )

        return issues

    def _check_grain_direction_compliance(
        self, placed_parts: list[PlacedPart]
    ) -> list[QualityIssue]:
        """Check grain direction compliance (placeholder for future implementation)."""
        # This would integrate with the grain direction system
        return []

    def _rectangles_overlap(
        self,
        rect1: tuple[float, float, float, float],
        rect2: tuple[float, float, float, float],
    ) -> bool:
        """Check if two rectangles overlap."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        return not (x1 >= x2 + w2 or x2 >= x1 + w1 or y1 >= y2 + h2 or y2 >= y1 + h1)

    def _calculate_overlap_area(
        self,
        rect1: tuple[float, float, float, float],
        rect2: tuple[float, float, float, float],
    ) -> float:
        """Calculate the area of overlap between two rectangles."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # Calculate intersection
        left = max(x1, x2)
        right = min(x1 + w1, x2 + w2)
        bottom = max(y1, y2)
        top = min(y1 + h1, y2 + h2)

        if left < right and bottom < top:
            return (right - left) * (top - bottom)
        return 0.0

    def _get_overlap_bounds(
        self,
        rect1: tuple[float, float, float, float],
        rect2: tuple[float, float, float, float],
    ) -> tuple[float, float, float, float]:
        """Get the bounding box of the overlap area."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        left = max(x1, x2)
        right = min(x1 + w1, x2 + w2)
        bottom = max(y1, y2)
        top = min(y1 + h1, y2 + h2)

        return (left, bottom, right - left, top - bottom)

    def _calculate_min_distance(
        self,
        rect1: tuple[float, float, float, float],
        rect2: tuple[float, float, float, float],
    ) -> float:
        """Calculate minimum distance between two rectangles."""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2

        # If rectangles overlap, distance is 0
        if self._rectangles_overlap(rect1, rect2):
            return 0.0

        # Calculate distances in each direction
        dx = max(0, max(x1 - (x2 + w2), x2 - (x1 + w1)))
        dy = max(0, max(y1 - (y2 + h2), y2 - (y1 + h1)))

        # Return Euclidean distance
        return (dx * dx + dy * dy) ** 0.5

    def _calculate_quality_metrics(
        self,
        placed_parts: list[PlacedPart],
        sheet_sizes: list[tuple[float, float]],
        issues: list[QualityIssue],
    ) -> dict[str, float]:
        """Calculate quality metrics for the layout."""
        metrics = {}

        # Count issues by severity
        critical_count = len(
            [i for i in issues if i.severity == QualitySeverity.CRITICAL]
        )
        warning_count = len(
            [i for i in issues if i.severity == QualitySeverity.WARNING]
        )
        info_count = len([i for i in issues if i.severity == QualitySeverity.INFO])

        metrics["critical_issues"] = critical_count
        metrics["warning_issues"] = warning_count
        metrics["info_issues"] = info_count
        metrics["total_issues"] = len(issues)

        # Calculate issue density (issues per part)
        metrics["issue_density"] = (
            len(issues) / len(placed_parts) if placed_parts else 0
        )

        # Calculate material utilization
        if sheet_sizes and placed_parts:
            total_part_area = sum(part.width * part.height for part in placed_parts)
            sheets_used = len(set(part.sheet_index for part in placed_parts))

            total_sheet_area = 0
            for sheet_idx in range(sheets_used):
                if sheet_idx < len(sheet_sizes):
                    w, h = sheet_sizes[sheet_idx]
                else:
                    w, h = sheet_sizes[-1]
                total_sheet_area += w * h

            metrics["material_utilization"] = (
                (total_part_area / total_sheet_area) * 100
                if total_sheet_area > 0
                else 0
            )
        else:
            metrics["material_utilization"] = 0

        # Calculate spacing compliance rate
        spacing_violations = len(
            [i for i in issues if i.issue_type == QualityIssueType.INSUFFICIENT_SPACING]
        )
        total_part_pairs = len(placed_parts) * (len(placed_parts) - 1) // 2
        metrics["spacing_compliance_rate"] = (
            ((total_part_pairs - spacing_violations) / total_part_pairs * 100)
            if total_part_pairs > 0
            else 100
        )

        return metrics

    def _calculate_overall_score(
        self, issues: list[QualityIssue], passed_checks: int, failed_checks: int
    ) -> float:
        """Calculate overall quality score (0-100)."""
        base_score = 100.0

        # Deduct points for issues
        for issue in issues:
            if issue.severity == QualitySeverity.CRITICAL:
                base_score -= 20
            elif issue.severity == QualitySeverity.WARNING:
                base_score -= 10
            elif issue.severity == QualitySeverity.INFO:
                base_score -= 2

        # Bonus for passed checks
        total_checks = passed_checks + failed_checks
        if total_checks > 0:
            check_bonus = (passed_checks / total_checks) * 10
            base_score += check_bonus

        return max(0.0, min(100.0, base_score))


def generate_quality_report_text(report: QualityReport) -> str:
    """Generate a human-readable quality report."""
    lines = []
    lines.append("SquatchCut Quality Assurance Report")
    lines.append("=" * 40)
    lines.append(f"Layout ID: {report.layout_id}")
    lines.append(f"Timestamp: {report.timestamp}")
    lines.append(f"Overall Score: {report.overall_score:.1f}/100")
    lines.append("")

    lines.append("Layout Summary:")
    lines.append(f"  Total Parts: {report.total_parts}")
    lines.append(f"  Total Sheets: {report.total_sheets}")
    lines.append(
        f"  Material Utilization: {report.metrics.get('material_utilization', 0):.1f}%"
    )
    lines.append("")

    lines.append("Quality Checks:")
    lines.append(f"  Passed: {len(report.passed_checks)}")
    lines.append(f"  Failed: {len(report.failed_checks)}")
    if report.passed_checks:
        lines.append(f"  Passed checks: {', '.join(report.passed_checks)}")
    if report.failed_checks:
        lines.append(f"  Failed checks: {', '.join(report.failed_checks)}")
    lines.append("")

    if report.issues:
        lines.append(f"Issues Found ({len(report.issues)} total):")

        # Group by severity
        critical = [i for i in report.issues if i.severity == QualitySeverity.CRITICAL]
        warnings = [i for i in report.issues if i.severity == QualitySeverity.WARNING]
        info = [i for i in report.issues if i.severity == QualitySeverity.INFO]

        if critical:
            lines.append(f"  CRITICAL ({len(critical)}):")
            for issue in critical:
                lines.append(f"    - {issue.description}")
                if issue.suggested_fix:
                    lines.append(f"      Fix: {issue.suggested_fix}")

        if warnings:
            lines.append(f"  WARNINGS ({len(warnings)}):")
            for issue in warnings:
                lines.append(f"    - {issue.description}")
                if issue.suggested_fix:
                    lines.append(f"      Fix: {issue.suggested_fix}")

        if info:
            lines.append(f"  INFO ({len(info)}):")
            for issue in info:
                lines.append(f"    - {issue.description}")
    else:
        lines.append("No issues found - excellent quality!")

    return "\n".join(lines)


def check_nesting_quality(
    placed_parts: list[PlacedPart],
    sheet_sizes: list[tuple[float, float]],
    min_spacing: float = 3.0,
    original_parts: list | None = None,
) -> QualityReport:
    """High-level function to check nesting quality."""
    checker = QualityAssuranceChecker(min_spacing=min_spacing)
    report = checker.check_layout_quality(placed_parts, sheet_sizes, original_parts)

    logger.info(
        f"Quality check complete: {report.overall_score:.1f}/100 score, {len(report.issues)} issues found"
    )
    return report
