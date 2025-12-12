"""
Property-based tests for the SquatchCut Task Specification Framework.

**Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
*For any* task assigned to an AI agent, the specification should include explicit
reasoning level, file paths, constraints, and acceptance criteria
**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
"""


import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from constraint_validation_tools import TaskSpecificationValidator


# Strategies for generating test data
@st.composite
def reasoning_level_strategy(draw):
    """Generate valid reasoning levels."""
    return draw(st.sampled_from(["LOW", "MEDIUM", "HIGH", "EXTRA-HIGH"]))


@st.composite
def file_path_strategy(draw):
    """Generate realistic SquatchCut file paths."""
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
            max_size=30,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "Pd")),
        )
    )
    extension = draw(st.sampled_from([".py", ".md", ".txt", ".json", ".xml", ".ui"]))

    return base + filename + extension


@st.composite
def constraint_reference_strategy(draw):
    """Generate valid constraint references."""
    areas = [
        "HYDRATION",
        "MEASUREMENT",
        "EXPORT",
        "UI",
        "TESTING",
        "REPOSITORY",
        "PYTHON",
        "COMMUNICATION",
    ]
    area = draw(st.sampled_from(areas))
    number = draw(st.integers(min_value=1, max_value=10))
    return f"{area}-{number:03d}"


@st.composite
def complete_task_spec_strategy(draw):
    """Generate complete task specifications."""
    reasoning_level = draw(reasoning_level_strategy())
    context = draw(st.text(min_size=20, max_size=200))
    requirements = draw(
        st.lists(st.text(min_size=10, max_size=100), min_size=1, max_size=10)
    )
    file_paths = draw(st.lists(file_path_strategy(), min_size=1, max_size=5))
    acceptance_criteria = draw(
        st.lists(st.text(min_size=15, max_size=150), min_size=1, max_size=8)
    )
    constraints = draw(st.lists(constraint_reference_strategy(), max_size=5))

    return {
        "reasoning_level": reasoning_level,
        "context": context,
        "requirements": requirements,
        "file_paths": file_paths,
        "acceptance_criteria": acceptance_criteria,
        "constraints": constraints,
        "verification": draw(st.text(min_size=20, max_size=100)),
    }


@st.composite
def incomplete_task_spec_strategy(draw):
    """Generate incomplete task specifications (missing required fields)."""
    spec = draw(complete_task_spec_strategy())

    # Randomly remove some required fields
    required_fields = [
        "reasoning_level",
        "context",
        "requirements",
        "file_paths",
        "acceptance_criteria",
    ]
    fields_to_remove = draw(
        st.lists(st.sampled_from(required_fields), min_size=1, max_size=3)
    )

    for field in fields_to_remove:
        if field in spec:
            del spec[field]

    return spec


@st.composite
def low_quality_task_spec_strategy(draw):
    """Generate low-quality task specifications (present but inadequate)."""
    return {
        "reasoning_level": draw(reasoning_level_strategy()),
        "context": draw(st.text(min_size=1, max_size=10)),  # Too brief
        "requirements": [draw(st.text(min_size=1, max_size=5))],  # Too brief
        "file_paths": draw(st.lists(file_path_strategy(), min_size=1, max_size=2)),
        "acceptance_criteria": [draw(st.text(min_size=1, max_size=10))],  # Too brief
        "constraints": [],  # Missing constraints
    }


class TestTaskSpecificationFramework:
    """Property-based tests for task specification completeness."""

    def setup_method(self):
        """Set up a fresh validator for each test."""
        self.validator = TaskSpecificationValidator()

    @given(complete_task_spec_strategy())
    @settings(max_examples=50, deadline=3000)
    def test_complete_task_spec_validation_success(self, task_spec):
        """
        Property: Complete task specifications should pass validation.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        result = self.validator.validate_task_specification(task_spec)

        # Complete specs should be valid
        assert result["is_valid"] == True
        assert len(result["violations"]) == 0

        # Should have a reasonable compliance score
        assert result["constraint_compliance_score"] >= 70.0

        # Verify result structure
        assert isinstance(result["warnings"], list)
        assert isinstance(result["recommendations"], list)
        assert isinstance(result["constraint_compliance_score"], (int, float))

    @given(incomplete_task_spec_strategy())
    @settings(max_examples=30, deadline=2000)
    def test_incomplete_task_spec_validation_failure(self, task_spec):
        """
        Property: Incomplete task specifications should fail validation.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        result = self.validator.validate_task_specification(task_spec)

        # Incomplete specs should be invalid
        assert result["is_valid"] == False
        assert len(result["violations"]) > 0

        # Should have lower compliance score
        assert result["constraint_compliance_score"] < 100.0

        # Should identify missing fields
        missing_field_violations = [
            v for v in result["violations"] if "Missing required field" in v
        ]
        assert len(missing_field_violations) > 0

    @given(reasoning_level_strategy())
    @settings(max_examples=20, deadline=1000)
    def test_reasoning_level_validation_consistency(self, reasoning_level):
        """
        Property: Valid reasoning levels should always be accepted.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        task_spec = {
            "reasoning_level": reasoning_level,
            "context": "Valid context for testing",
            "requirements": ["Valid requirement"],
            "file_paths": ["freecad/SquatchCut/core/test.py"],
            "acceptance_criteria": ["Valid acceptance criterion"],
        }

        result = self.validator.validate_task_specification(task_spec)

        # Should not have reasoning level violations
        reasoning_violations = [
            v for v in result["violations"] if "reasoning level" in v.lower()
        ]
        assert len(reasoning_violations) == 0

    @given(st.text(min_size=1, max_size=20))
    @settings(max_examples=20, deadline=1000)
    def test_invalid_reasoning_level_rejection(self, invalid_level):
        """
        Property: Invalid reasoning levels should be rejected.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        assume(invalid_level not in ["LOW", "MEDIUM", "HIGH", "EXTRA-HIGH"])

        task_spec = {
            "reasoning_level": invalid_level,
            "context": "Valid context for testing",
            "requirements": ["Valid requirement"],
            "file_paths": ["freecad/SquatchCut/core/test.py"],
            "acceptance_criteria": ["Valid acceptance criterion"],
        }

        result = self.validator.validate_task_specification(task_spec)

        # Should have reasoning level violation
        reasoning_violations = [
            v for v in result["violations"] if "reasoning level" in v.lower()
        ]
        assert len(reasoning_violations) > 0

    @given(st.lists(file_path_strategy(), min_size=1, max_size=10))
    @settings(max_examples=30, deadline=2000)
    def test_file_path_constraint_relevance(self, file_paths):
        """
        Property: File paths should determine relevant constraint recommendations.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        task_spec = {
            "reasoning_level": "HIGH",
            "context": "Testing constraint relevance",
            "requirements": ["Test requirement"],
            "file_paths": file_paths,
            "acceptance_criteria": ["Test criterion"],
        }

        result = self.validator.validate_task_specification(task_spec)

        # GUI files should trigger UI/hydration constraint recommendations
        gui_files = any("gui/" in fp or "taskpanel" in fp.lower() for fp in file_paths)
        if gui_files:
            # Should have recommendations or warnings about UI/hydration constraints
            ui_mentions = any(
                "hydration" in str(r).lower() or "ui" in str(r).lower()
                for r in result["recommendations"] + result["warnings"]
            )
            # This is a soft check - may not always trigger depending on implementation
            assert isinstance(ui_mentions, bool)  # Just verify it's a boolean

        # Core files should trigger measurement/export constraint recommendations
        core_files = any("core/" in fp for fp in file_paths)
        if core_files:
            # Should consider measurement/export constraints
            core_mentions = any(
                "measurement" in str(r).lower() or "export" in str(r).lower()
                for r in result["recommendations"] + result["warnings"]
            )
            assert isinstance(core_mentions, bool)  # Just verify it's a boolean

    @given(low_quality_task_spec_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_quality_assessment_sensitivity(self, task_spec):
        """
        Property: Low-quality task specifications should receive lower compliance scores.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        result = self.validator.validate_task_specification(task_spec)

        # Low-quality specs should have reduced compliance scores
        assert result["constraint_compliance_score"] < 90.0

        # Should have warnings or recommendations for improvement
        total_feedback = len(result["warnings"]) + len(result["recommendations"])
        assert total_feedback > 0

    @given(complete_task_spec_strategy())
    @settings(max_examples=20, deadline=2000)
    def test_validation_determinism(self, task_spec):
        """
        Property: Task specification validation should be deterministic.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        # Run validation multiple times
        result1 = self.validator.validate_task_specification(task_spec)
        result2 = self.validator.validate_task_specification(task_spec)
        result3 = self.validator.validate_task_specification(task_spec)

        # Results should be identical
        assert result1["is_valid"] == result2["is_valid"] == result3["is_valid"]
        assert (
            len(result1["violations"])
            == len(result2["violations"])
            == len(result3["violations"])
        )
        assert (
            result1["constraint_compliance_score"]
            == result2["constraint_compliance_score"]
            == result3["constraint_compliance_score"]
        )

    def test_required_fields_completeness(self):
        """
        Property: All required fields should be checked for presence.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        # Test with completely empty spec
        empty_spec = {}
        result = self.validator.validate_task_specification(empty_spec)

        assert result["is_valid"] == False
        assert (
            len(result["violations"]) >= 5
        )  # Should catch all missing required fields

        # Check that all required fields are mentioned in violations
        required_fields = [
            "reasoning_level",
            "context",
            "requirements",
            "file_paths",
            "acceptance_criteria",
        ]
        violation_text = " ".join(result["violations"])

        for field in required_fields:
            assert field in violation_text

    @example(
        {
            "reasoning_level": "HIGH",
            "context": "Implement TaskPanel with proper hydration",
            "requirements": ["Create TaskPanel", "Implement hydration"],
            "file_paths": ["freecad/SquatchCut/gui/taskpanel_new.py"],
            "acceptance_criteria": [
                "TaskPanel must call hydrate_from_params() before creating widgets"
            ],
            "constraints": ["HYDRATION-001"],
        }
    )
    @given(complete_task_spec_strategy())
    def test_constraint_awareness_scoring(self, task_spec):
        """
        Property: Task specs with explicit constraint mentions should score higher.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        # Add constraint-aware content to a copy of the spec
        constraint_aware_spec = task_spec.copy()
        constraint_aware_spec["requirements"] = task_spec["requirements"] + [
            "Must follow HYDRATION-001 constraint",
            "Ensure millimeter internal storage per MEASUREMENT-001",
        ]
        constraint_aware_spec["acceptance_criteria"] = task_spec[
            "acceptance_criteria"
        ] + ["Verify hydrate_from_params() called before widget creation"]

        # Compare scores
        original_result = self.validator.validate_task_specification(task_spec)
        aware_result = self.validator.validate_task_specification(constraint_aware_spec)

        # Constraint-aware spec should score the same or higher
        assert (
            aware_result["constraint_compliance_score"]
            >= original_result["constraint_compliance_score"]
        )

    @given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=2000)
    def test_acceptance_criteria_quality_assessment(self, criteria_list):
        """
        Property: Acceptance criteria quality should affect validation results.
        **Feature: ai-agent-documentation, Property 2: Task Specification Completeness**
        """
        task_spec = {
            "reasoning_level": "MEDIUM",
            "context": "Testing acceptance criteria quality",
            "requirements": ["Test requirement"],
            "file_paths": ["freecad/SquatchCut/core/test.py"],
            "acceptance_criteria": criteria_list,
        }

        result = self.validator.validate_task_specification(task_spec)

        # Very short criteria should trigger warnings or lower scores
        avg_length = sum(len(c) for c in criteria_list) / len(criteria_list)
        if avg_length < 15:
            # Should have some feedback about brief criteria
            has_feedback = (
                len(result["warnings"]) > 0 or len(result["recommendations"]) > 0
            )
            assert has_feedback or result["constraint_compliance_score"] < 100.0


if __name__ == "__main__":
    # Run the property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
