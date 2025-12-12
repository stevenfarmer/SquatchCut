"""Tests for quality assurance functionality."""

import pytest
from unittest.mock import Mock, patch
import datetime

from SquatchCut.core.quality_assurance import (
    QualityIssueType,
    QualitySeverity,
    QualityIssue,
    QualityReport,
    QualityAssuranceChecker,
    generate_quality_report_text,
    check_nesting_quality,
)
from SquatchCut.core.nesting import PlacedPart


class TestQualityEnums:
    """Test quality-related enumerations."""

    def test_quality_issue_type_values(self):
        """Test quality issue type enum values."""
        assert QualityIssueType.OVERLAP.value == "overlap"
        assert QualityIssueType.OUT_OF_BOUNDS.value == "out_of_bounds"
        assert QualityIssueType.INSUFFICIENT_SPACING.value == "insufficient_spacing"
        assert QualityIssueType.ROTATION_ERROR.value == "rotation_error"
        assert QualityIssueType.DIMENSION_MISMATCH.value == "dimension_mismatch"
        assert QualityIssueType.GRAIN_VIOLATION.value == "grain_violation"

    def test_quality_severity_values(self):
        """Test quality severity enum values."""
        assert QualitySeverity.CRITICAL.value == "critical"
        assert QualitySeverity.WARNING.value == "warning"
        assert QualitySeverity.INFO.value == "info"


class TestQualityIssue:
    """Test quality issue data structure."""

    def test_quality_issue_creation(self):
        """Test creating a quality issue."""
        issue = QualityIssue(
            issue_type=QualityIssueType.OVERLAP,
            severity=QualitySeverity.CRITICAL,
            part_ids=["A", "B"],
            sheet_index=0,
            description="Parts A and B overlap",
            suggested_fix="Adjust positions",
            coordinates=(100.0, 50.0),
            affected_area=(90.0, 40.0, 20.0, 20.0),
        )

        assert issue.issue_type == QualityIssueType.OVERLAP
        assert issue.severity == QualitySeverity.CRITICAL
        assert issue.part_ids == ["A", "B"]
        assert issue.sheet_index == 0
        assert issue.description == "Parts A and B overlap"
        assert issue.suggested_fix == "Adjust positions"
        assert issue.coordinates == (100.0, 50.0)
        assert issue.affected_area == (90.0, 40.0, 20.0, 20.0)

    def test_quality_issue_defaults(self):
        """Test quality issue with default values."""
        issue = QualityIssue(
            issue_type=QualityIssueType.ROTATION_ERROR,
            severity=QualitySeverity.WARNING,
            part_ids=["C"],
            sheet_index=1,
            description="Invalid rotation",
        )

        assert issue.suggested_fix == ""
        assert issue.coordinates is None
        assert issue.affected_area is None


class TestQualityReport:
    """Test quality report data structure."""

    def test_quality_report_creation(self):
        """Test creating a quality report."""
        issues = [
            QualityIssue(
                QualityIssueType.OVERLAP,
                QualitySeverity.CRITICAL,
                ["A", "B"],
                0,
                "Overlap detected",
            )
        ]

        report = QualityReport(
            layout_id="test_layout",
            timestamp="2024-01-01T12:00:00",
            total_parts=5,
            total_sheets=2,
            issues=issues,
            metrics={"utilization": 85.5},
            passed_checks=["bounds_check"],
            failed_checks=["overlap_check"],
            overall_score=75.0,
        )

        assert report.layout_id == "test_layout"
        assert report.timestamp == "2024-01-01T12:00:00"
        assert report.total_parts == 5
        assert report.total_sheets == 2
        assert len(report.issues) == 1
        assert report.metrics["utilization"] == 85.5
        assert report.passed_checks == ["bounds_check"]
        assert report.failed_checks == ["overlap_check"]
        assert report.overall_score == 75.0


class TestQualityAssuranceChecker:
    """Test quality assurance checker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = QualityAssuranceChecker(
            min_spacing=5.0, tolerance=0.1, check_grain_direction=False
        )

        # Create test placed parts
        self.placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=110, y=0, width=80, height=60, sheet_index=0),
            PlacedPart(id="C", x=0, y=60, width=120, height=40, sheet_index=0),
        ]

        self.sheet_sizes = [(300, 200)]

    def test_checker_initialization(self):
        """Test checker initialization."""
        assert self.checker.min_spacing == 5.0
        assert self.checker.tolerance == 0.1
        assert self.checker.check_grain_direction is False

    def test_check_overlaps_no_overlap(self):
        """Test overlap detection with no overlaps."""
        issues = self.checker._check_overlaps(self.placed_parts)
        assert len(issues) == 0

    def test_check_overlaps_with_overlap(self):
        """Test overlap detection with overlapping parts."""
        overlapping_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=100, sheet_index=0),
            PlacedPart(
                id="B", x=50, y=50, width=100, height=100, sheet_index=0
            ),  # Overlaps A
        ]

        issues = self.checker._check_overlaps(overlapping_parts)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == QualityIssueType.OVERLAP
        assert issue.severity == QualitySeverity.CRITICAL
        assert set(issue.part_ids) == {"A", "B"}
        assert issue.sheet_index == 0
        assert "overlap" in issue.description.l

    def test_check_bounds_compliance_valid(self):
        """Test bounds compliance with valid parts."""
        issues = self.checker._check_bounds_compliance(
            self.placed_parts, self.sheet_sizes
        )
        assert len(issues) == 0

    def test_check_bounds_compliance_out_of_bounds(self):
        """Test bounds compliance with out-of-bounds parts."""
        out_of_bounds_parts = [
            PlacedPart(
                id="A", x=250, y=0, width=100, height=50, sheet_index=0
            ),  # Exceeds width
            PlacedPart(
                id="B", x=0, y=180, width=80, height=50, sheet_index=0
            ),  # Exceeds height
        ]

        issues = self.checker._check_bounds_compliance(
            out_of_bounds_parts, self.sheet_sizes
        )

        assert len(issues) == 2

        for issue in issues:
            assert issue.issue_type == QualityIssueType.OUT_OF_BOUNDS
            assert issue.severity == QualitySeverity.CRITICAL
            assert "beyond sheet boundaries" in issue.description

    def test_check_spacing_requirements_sufficient(self):
        """Test spacing requirements with sufficient spacing."""
        issues = self.checker._check_spacing_requirements(self.placed_parts)
        assert len(issues) == 0  # Parts should have sufficient spacing

    def test_check_spacing_requirements_insufficient(self):
        """Test spacing requirements with insufficient spacing."""
        close_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(
                id="B", x=102, y=0, width=80, height=60, sheet_index=0
            ),  # Only 2mm gap
        ]

        issues = self.checker._check_spacing_requirements(close_parts)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == QualityIssueType.INSUFFICIENT_SPACING
        assert issue.severity == QualitySeverity.WARNING
        assert set(issue.part_ids) == {"A", "B"}

    def test_check_rotation_consistency_valid(self):
        """Test rotation consistency with valid rotations."""
        issues = self.checker._check_rotation_consistency(self.placed_parts)
        assert len(issues) == 0  # Default rotation is 0, which is valid

    def test_check_rotation_consistency_invalid(self):
        """Test rotation consistency with invalid rotations."""
        invalid_rotation_parts = [
            PlacedPart(
                id="A", x=0, y=0, width=100, height=50, rotation_deg=45, sheet_index=0
            )  # Invalid
        ]

        issues = self.checker._check_rotation_consistency(invalid_rotation_parts)

        assert len(issues) == 1
        issue = issues[0]
        assert issue.issue_type == QualityIssueType.ROTATION_ERROR
        assert issue.severity == QualitySeverity.WARNING
        assert issue.part_ids == ["A"]
        assert "45°" in issue.description

    def test_rectangles_overlap_detection(self):
        """Test rectangle overlap detection utility."""
        rect1 = (0, 0, 100, 50)
        rect2 = (50, 25, 100, 50)  # Overlaps
        rect3 = (150, 0, 100, 50)  # No overlap

        assert self.checker._rectangles_overlap(rect1, rect2) is True
        assert self.checker._rectangles_overlap(rect1, rect3) is False

    def test_calculate_overlap_area(self):
        """Test overlap area calculation."""
        rect1 = (0, 0, 100, 100)
        rect2 = (50, 50, 100, 100)  # 50x50 overlap

        area = self.checker._calculate_overlap_area(rect1, rect2)
        assert area == 2500  # 50 * 50

    def test_calculate_min_distance(self):
        """Test minimum distance calculation."""
        rect1 = (0, 0, 100, 50)
        rect2 = (110, 0, 80, 60)  # 10mm gap horizontally

        distance = self.checker._calculate_min_distance(rect1, rect2)
        assert distance == 10.0

    def test_calculate_min_distance_overlapping(self):
        """Test minimum distance for overlapping rectangles."""
        rect1 = (0, 0, 100, 50)
        rect2 = (50, 25, 100, 50)  # Overlapping

        distance = self.checker._calculate_min_distance(rect1, rect2)
        assert distance == 0.0

    @patch("datetime.datetime")
    def test_check_layout_quality_comprehensive(self, mock_datetime):
        """Test comprehensive layout quality check."""
        # Mock datetime for consistent testing
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"

        report = self.checker.check_layout_quality(self.placed_parts, self.sheet_sizes)

        assert isinstance(report, QualityReport)
        assert report.total_parts == len(self.placed_parts)
        assert report.total_sheets == 1
        assert isinstance(report.issues, list)
        assert isinstance(report.metrics, dict)
        assert isinstance(report.passed_checks, list)
        assert isinstance(report.failed_checks, list)
        assert 0 <= report.overall_score <= 100

    def test_calculate_quality_metrics(self):
        """Test quality metrics calculation."""
        issues = [
            QualityIssue(
                QualityIssueType.OVERLAP,
                QualitySeverity.CRITICAL,
                ["A", "B"],
                0,
                "Test",
            ),
            QualityIssue(
                QualityIssueType.INSUFFICIENT_SPACING,
                QualitySeverity.WARNING,
                ["C", "D"],
                0,
                "Test",
            ),
        ]

        metrics = self.checker._calculate_quality_metrics(
            self.placed_parts, self.sheet_sizes, issues
        )

        assert "critical_issues" in metrics
        assert "warning_issues" in metrics
        assert "info_issues" in metrics
        assert "total_issues" in metrics
        assert "issue_density" in metrics
        assert "material_utilization" in metrics
        assert "spacing_compliance_rate" in metrics

        assert metrics["critical_issues"] == 1
        assert metrics["warning_issues"] == 1
        assert metrics["total_issues"] == 2
        assert metrics["issue_density"] > 0

    def test_calculate_overall_score(self):
        """Test overall score calculation."""
        # No issues, all checks passed
        score = self.checker._calculate_overall_score([], 5, 0)
        assert score > 90  # Should be high score

        # Critical issues
        critical_issues = [
            QualityIssue(
                QualityIssueType.OVERLAP, QualitySeverity.CRITICAL, ["A"], 0, "Test"
            ),
            QualityIssue(
                QualityIssueType.OUT_OF_BOUNDS,
                QualitySeverity.CRITICAL,
                ["B"],
                0,
                "Test",
            ),
        ]
        score = self.checker._calculate_overall_score(critical_issues, 3, 2)
        assert score < 70  # Should be lower due to critical issues

        # Warning issues
        warning_issues = [
            QualityIssue(
                QualityIssueType.INSUFFICIENT_SPACING,
                QualitySeverity.WARNING,
                ["A"],
                0,
                "Test",
            )
        ]
        score = self.checker._calculate_overall_score(warning_issues, 4, 1)
        assert 80 <= score <= 95  # Moderate score for warnings


class TestQualityReportGeneration:
    """Test quality report text generation."""

    def test_generate_quality_report_text_no_issues(self):
        """Test generating report text with no issues."""
        report = QualityReport(
            layout_id="test_layout",
            timestamp="2024-01-01T12:00:00",
            total_parts=3,
            total_sheets=1,
            issues=[],
            metrics={"material_utilization": 85.5},
            passed_checks=["overlap_detection", "bounds_compliance"],
            failed_checks=[],
            overall_score=95.0,
        )

        text = generate_quality_report_text(report)

        assert "SquatchCut Quality Assurance Report" in text
        assert "Overall Score: 95.0/100" in text
        assert "Total Parts: 3" in text
        assert "Total Sheets: 1" in text
        assert "Passed: 2" in text
        assert "Failed: 0" in text
        assert "No issues found - excellent quality!" in text

    def test_generate_quality_report_text_with_issues(self):
        """Test generating report text with issues."""
        issues = [
            QualityIssue(
                QualityIssueType.OVERLAP,
                QualitySeverity.CRITICAL,
                ["A", "B"],
                0,
                "Parts A and B overlap",
                suggested_fix="Adjust positions",
            ),
            QualityIssue(
                QualityIssueType.INSUFFICIENT_SPACING,
                QualitySeverity.WARNING,
                ["C", "D"],
                0,
                "Insufficient spacing between C and D",
                suggested_fix="Increase spacing",
            ),
        ]

        report = QualityReport(
            layout_id="test_layout",
            timestamp="2024-01-01T12:00:00",
            total_parts=4,
            total_sheets=1,
            issues=issues,
            metrics={"material_utilization": 75.0},
            passed_checks=["bounds_compliance"],
            failed_checks=["overlap_detection", "spacing_requirements"],
            overall_score=65.0,
        )

        text = generate_quality_report_text(report)

        assert "Overall Score: 65.0/100" in text
        assert "Issues Found (2 total)" in text
        assert "CRITICAL (1)" in text
        assert "WARNINGS (1)" in text
        assert "Parts A and B overlap" in text
        assert "Insufficient spacing between C and D" in text
        assert "Fix: Adjust positions" in text
        assert "Fix: Increase spacing" in text


class TestHighLevelFunction:
    """Test high-level quality checking function."""

    def test_check_nesting_quality(self):
        """Test high-level quality checking function."""
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0),
            PlacedPart(id="B", x=110, y=0, width=80, height=60, sheet_index=0),
        ]

        sheet_sizes = [(300, 200)]

        with patch("SquatchCut.core.quality_assurance.logger") as mock_logger:
            report = check_nesting_quality(placed_parts, sheet_sizes, min_spacing=5.0)

        assert isinstance(report, QualityReport)
        assert report.total_parts == 2
        assert report.total_sheets == 1

        # Should log completion
        mock_logger.info.assert_called()

    def test_check_nesting_quality_with_original_parts(self):
        """Test quality checking with original parts for dimension validation."""
        placed_parts = [
            PlacedPart(id="A", x=0, y=0, width=100, height=50, sheet_index=0)
        ]

        # Mock original parts
        original_parts = [Mock()]
        original_parts[0].id = "A"
        original_parts[0].width = 100
        original_parts[0].height = 50

        sheet_sizes = [(300, 200)]

        report = check_nesting_quality(
            placed_parts, sheet_sizes, original_parts=original_parts
        )

        # Should pass dimension consistency check
        assert "dimension_consistency" in report.passed_checks


class TestQualityAssuranceIntegration:
    """Integration tests for quality assurance."""

    def test_comprehensive_quality_check(self):
        """Test comprehensive quality check with various issues."""
        placed_parts = [
            # Good part
            PlacedPart(id="Good", x=0, y=0, width=100, height=50, sheet_index=0),
            # Overlapping part
            PlacedPart(id="Overlap1", x=80, y=30, width=100, height=50, sheet_index=0),
            PlacedPart(id="Overlap2", x=120, y=40, width=100, height=50, sheet_index=0),
            # Out of bounds part
            PlacedPart(
                id="OutOfBounds", x=250, y=0, width=100, height=50, sheet_index=0
            ),
            # Invalid rotation
            PlacedPart(
                id="BadRotation",
                x=0,
                y=100,
                width=80,
                height=40,
                rotation_deg=45,
                sheet_index=0,
            ),
            # Too close spacing
            PlacedPart(id="Close1", x=0, y=150, width=50, height=30, sheet_index=0),
            PlacedPart(
                id="Close2", x=52, y=150, width=50, height=30, sheet_index=0
            ),  # 2mm gap
        ]

        sheet_sizes = [(300, 200)]

        checker = QualityAssuranceChecker(min_spacing=5.0, tolerance=0.1)
        report = checker.check_layout_quality(placed_parts, sheet_sizes)

        # Should find multiple types of issues
        issue_types = {issue.issue_type for issue in report.issues}

        assert QualityIssueType.OVERLAP in issue_types
        assert QualityIssueType.OUT_OF_BOUNDS in issue_types
        assert QualityIssueType.ROTATION_ERROR in issue_types
        assert QualityIssueType.INSUFFICIENT_SPACING in issue_types

        # Should have failed multiple checks
        assert len(report.failed_checks) > 0

        # Overall score should be low due to multiple issues
        assert report.overall_score < 50

        # Should have reasonable metrics
        assert report.metrics["critical_issues"] > 0
        assert report.metrics["warning_issues"] > 0
        assert report.metrics["total_issues"] > 3

    def test_perfect_layout_quality(self):
        """Test quality check with a perfect layout."""
        placed_parts = [
            PlacedPart(id="A", x=10, y=10, width=80, height=40, sheet_index=0),
            PlacedPart(id="B", x=100, y=10, width=80, height=40, sheet_index=0),
            PlacedPart(id="C", x=10, y=60, width=80, height=40, sheet_index=0),
            PlacedPart(id="D", x=100, y=60, width=80, height=40, sheet_index=0),
        ]

        sheet_sizes = [(200, 120)]

        checker = QualityAssuranceChecker(min_spacing=5.0)
        report = checker.check_layout_quality(placed_parts, sheet_sizes)

        # Should have no issues
        assert len(report.issues) == 0

        # Should pass all checks
        assert len(report.failed_checks) == 0
        assert len(report.passed_checks) > 0

        # Should have high score
        assert report.overall_score > 90

        # Should have good utilization
        assert report.metrics["material_utilization"] > 50
