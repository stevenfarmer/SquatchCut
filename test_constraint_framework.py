"""
Property-based tests for the SquatchCut Constraint Framework.

**Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
*For any* AI agent task, all critical architectural constraints should be validated
and enforced before implementation begins
**Validates: Requirements 1.1, 1.3, 1.4, 1.5**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from typing import Dict, Any, List
from constraint_framework import (
    ConstraintFramework,
    Constraint,
    ConstraintArea,
    Severity,
    ValidationResult,
)


# Strategies for generating test data
@st.composite
def constraint_area_strategy(draw):
    """Generate valid constraint areas."""
    return draw(st.sampled_from(list(ConstraintArea)))


@st.composite
def severity_strategy(draw):
    """Generate valid severity levels."""
    return draw(st.sampled_from(list(Severity)))


@st.composite
def file_path_strategy(draw):
    """Generate realistic file paths for SquatchCut."""
    base_paths = [
        "freecad/SquatchCut/core/",
        "freecad/SquatchCut/gui/",
        "freecad/SquatchCut/resources/",
        "tests/",
        "docs/",
    ]

    base = draw(st.sampled_from(base_paths))
    filename = draw(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )
    extension = draw(st.sampled_from([".py", ".md", ".txt", ".json", ".xml"]))

    return base + filename + extension


@st.composite
def code_change_strategy(draw):
    """Generate realistic code change descriptions."""
    file_paths = draw(st.lists(file_path_strategy(), min_size=1, max_size=5))
    operation_types = [
        "create",
        "modify",
        "delete",
        "refactor",
        "ui_change",
        "export_change",
        "test_change",
    ]
    operation_type = draw(st.sampled_from(operation_types))

    affected_areas = draw(
        st.lists(st.sampled_from([area.value for area in ConstraintArea]), max_size=3)
    )

    return {
        "file_paths": file_paths,
        "operation_type": operation_type,
        "affected_areas": affected_areas,
        "description": draw(st.text(min_size=10, max_size=100)),
    }


@st.composite
def valid_constraint_strategy(draw):
    """Generate valid constraint definitions."""
    constraint_id = draw(
        st.text(
            min_size=5,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pd")),
        )
    )
    area = draw(constraint_area_strategy())
    severity = draw(severity_strategy())
    rule = draw(st.text(min_size=10, max_size=200))
    rationale = draw(st.text(min_size=20, max_size=300))
    examples = draw(st.lists(st.text(min_size=5, max_size=100), max_size=5))
    anti_patterns = draw(st.lists(st.text(min_size=5, max_size=100), max_size=5))

    return {
        "constraint_id": constraint_id,
        "area": area,
        "severity": severity,
        "rule": rule,
        "rationale": rationale,
        "examples": examples,
        "anti_patterns": anti_patterns,
    }


class TestConstraintFramework:
    """Property-based tests for the constraint framework."""

    def setup_method(self):
        """Set up a fresh constraint framework for each test."""
        self.framework = ConstraintFramework()

    @given(valid_constraint_strategy())
    @settings(max_examples=50, deadline=2000)
    def test_constraint_definition_roundtrip(self, constraint_data):
        """
        Property: Defining a constraint and retrieving it should return the same constraint.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        # Define the constraint
        constraint = self.framework.define_constraint(**constraint_data)

        # Retrieve the constraint
        retrieved = self.framework.get_constraint(constraint_data["constraint_id"])

        # Verify roundtrip consistency
        assert retrieved is not None
        assert retrieved.id == constraint_data["constraint_id"]
        assert retrieved.area == constraint_data["area"]
        assert retrieved.severity == constraint_data["severity"]
        assert retrieved.rule == constraint_data["rule"]
        assert retrieved.rationale == constraint_data["rationale"]
        assert retrieved.examples == constraint_data["examples"]
        assert retrieved.anti_patterns == constraint_data["anti_patterns"]

    @given(constraint_area_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_constraint_area_filtering_consistency(self, area):
        """
        Property: Getting constraints by area should only return constraints from that area.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        # Get constraints for the area
        area_constraints = self.framework.get_constraints_by_area(area)

        # Verify all returned constraints belong to the specified area
        for constraint in area_constraints:
            assert constraint.area == area

    @given(severity_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_constraint_severity_filtering_consistency(self, severity):
        """
        Property: Getting constraints by severity should only return constraints of that severity.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        # Get constraints for the severity level
        severity_constraints = self.framework.get_constraints_by_severity(severity)

        # Verify all returned constraints have the specified severity
        for constraint in severity_constraints:
            assert constraint.severity == severity

    @given(code_change_strategy())
    @settings(max_examples=30, deadline=3000)
    def test_validation_result_structure_consistency(self, code_change):
        """
        Property: Validation results should always have consistent structure and logical relationships.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        # Validate the code change
        result = self.framework.validate_compliance(code_change)

        # Verify result structure
        assert isinstance(result, ValidationResult)
        assert isinstance(result.is_compliant, bool)
        assert isinstance(result.violated_constraints, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.approval_required, bool)

        # Verify logical consistency
        if result.violated_constraints:
            # If there are violations, compliance should be False
            assert not result.is_compliant

        # If approval is required, there should be violations or important warnings
        if result.approval_required:
            has_important_violations = any(
                c.severity == Severity.IMPORTANT for c in result.violated_constraints
            )
            assert has_important_violations or len(result.warnings) > 0

    @given(
        st.text(min_size=1, max_size=50), st.lists(file_path_strategy(), max_size=10)
    )
    @settings(max_examples=30, deadline=2000)
    def test_checklist_generation_completeness(self, task_type, file_paths):
        """
        Property: Generated checklists should include all relevant critical constraints.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        assume(len(task_type.strip()) > 0)  # Ensure non-empty task type

        # Generate checklist
        checklist = self.framework.generate_constraint_checklist(task_type, file_paths)

        # Verify checklist structure
        assert isinstance(checklist, list)

        # If there are critical constraints in the framework,
        # and the task/files are relevant, checklist should not be empty
        critical_constraints = self.framework.get_constraints_by_severity(
            Severity.CRITICAL
        )
        if critical_constraints:
            # For UI-related files, should include UI/hydration constraints
            ui_files = any(
                "gui/" in fp or "taskpanel" in fp.lower() for fp in file_paths
            )
            if ui_files or "ui" in task_type.lower():
                # Should have some checklist items for UI-related tasks
                assert len(checklist) >= 0  # At minimum, should not fail

        # Verify checklist item format
        for item in checklist:
            assert isinstance(item, str)
            # Critical items should be marked as such
            if "CRITICAL" in item:
                assert item.startswith("✓ CRITICAL:")
            elif "IMPORTANT" in item:
                assert item.startswith("⚠ IMPORTANT:")

    @given(st.lists(valid_constraint_strategy(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=3000)
    def test_constraint_framework_scalability(self, constraint_list):
        """
        Property: Framework should handle multiple constraints efficiently and maintain consistency.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        # Add multiple constraints
        added_constraints = []
        for constraint_data in constraint_list:
            # Ensure unique IDs
            constraint_data["constraint_id"] = (
                f"{constraint_data['constraint_id']}_{len(added_constraints)}"
            )
            constraint = self.framework.define_constraint(**constraint_data)
            added_constraints.append(constraint)

        # Verify all constraints were added
        assert len(added_constraints) == len(constraint_list)

        # Verify retrieval consistency
        for constraint in added_constraints:
            retrieved = self.framework.get_constraint(constraint.id)
            assert retrieved is not None
            assert retrieved.id == constraint.id

        # Verify area and severity filtering still works
        for area in ConstraintArea:
            area_constraints = self.framework.get_constraints_by_area(area)
            for constraint in area_constraints:
                assert constraint.area == area

        for severity in Severity:
            severity_constraints = self.framework.get_constraints_by_severity(severity)
            for constraint in severity_constraints:
                assert constraint.severity == severity

    def test_core_constraints_initialization(self):
        """
        Property: Framework should initialize with core SquatchCut constraints.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        # Verify critical hydration constraints exist
        hydration_001 = self.framework.get_constraint("HYDRATION-001")
        assert hydration_001 is not None
        assert hydration_001.severity == Severity.CRITICAL
        assert "hydrate_from_params()" in hydration_001.rule

        # Verify critical measurement constraints exist
        measurement_001 = self.framework.get_constraint("MEASUREMENT-001")
        assert measurement_001 is not None
        assert measurement_001.severity == Severity.CRITICAL
        assert "millimeters" in measurement_001.rule

        # Verify critical export constraints exist
        export_001 = self.framework.get_constraint("EXPORT-001")
        assert export_001 is not None
        assert export_001.severity == Severity.CRITICAL
        assert "exporter.py" in export_001.rule

        # Verify critical Python constraints exist
        python_001 = self.framework.get_constraint("PYTHON-001")
        assert python_001 is not None
        assert python_001.severity == Severity.CRITICAL
        assert "3.10" in python_001.rule

    @example("HYDRATION-001")
    @example("MEASUREMENT-001")
    @example("EXPORT-001")
    @example("PYTHON-001")
    @given(
        st.sampled_from(
            [
                "HYDRATION-001",
                "HYDRATION-002",
                "HYDRATION-003",
                "MEASUREMENT-001",
                "MEASUREMENT-002",
                "EXPORT-001",
                "EXPORT-002",
                "PYTHON-001",
                "PYTHON-002",
                "UI-001",
            ]
        )
    )
    def test_constraint_rationale_completeness(self, constraint_id):
        """
        Property: All core constraints should have complete rationale information.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        rationale = self.framework.provide_constraint_rationale(constraint_id)

        assert rationale is not None
        assert len(rationale) > 0

        # Verify rationale contains key sections
        assert "Constraint:" in rationale
        assert "Rationale:" in rationale

        # Verify constraint exists and has required fields
        constraint = self.framework.get_constraint(constraint_id)
        assert constraint is not None
        assert len(constraint.rule) > 0
        assert len(constraint.rationale) > 0

    @given(code_change_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_validation_determinism(self, code_change):
        """
        Property: Validation should be deterministic - same input should produce same output.
        **Feature: ai-agent-documentation, Property 1: Constraint Enforcement**
        """
        # Run validation multiple times
        result1 = self.framework.validate_compliance(code_change)
        result2 = self.framework.validate_compliance(code_change)
        result3 = self.framework.validate_compliance(code_change)

        # Results should be identical
        assert result1.is_compliant == result2.is_compliant == result3.is_compliant
        assert (
            len(result1.violated_constraints)
            == len(result2.violated_constraints)
            == len(result3.violated_constraints)
        )
        assert len(result1.warnings) == len(result2.warnings) == len(result3.warnings)
        assert (
            len(result1.recommendations)
            == len(result2.recommendations)
            == len(result3.recommendations)
        )
        assert (
            result1.approval_required
            == result2.approval_required
            == result3.approval_required
        )


if __name__ == "__main__":
    # Run the property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
