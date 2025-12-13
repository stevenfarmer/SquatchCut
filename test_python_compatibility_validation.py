"""
Property-based tests for SquatchCut Python Compatibility Validation.

**Feature: ai-agent-documentation, Property 6: Python Compatibility Validation**
*For any* Python code written by AI agents, compatibility with Python versions
older than 3.10 should be enforced
**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**
"""

import ast
import re
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st


class PythonCompatibilityValidator:
    """Validates Python code for compatibility with versions < 3.10."""

    def __init__(self):
        self.compatibility_issues = []

    def validate_code(self, code: str) -> dict[str, Any]:
        """Validate Python code for compatibility issues."""
        issues = []

        try:
            # Parse the AST
            tree = ast.parse(code)

            # Check for AST-based issues
            issues.extend(self._check_ast_compatibility(tree))

            # Check for text-based issues
            issues.extend(self._check_text_compatibility(code))

        except SyntaxError as e:
            # Syntax errors might indicate compatibility issues
            issues.append(
                {
                    "type": "syntax_error",
                    "message": f"Syntax error: {e}",
                    "line": getattr(e, "lineno", "unknown"),
                }
            )

        return {
            "is_compatible": len(issues) == 0,
            "issues": issues,
            "total_issues": len(issues),
            "critical_issues": len(
                [i for i in issues if i.get("severity") == "critical"]
            ),
        }

    def _check_ast_compatibility(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Check AST for compatibility issues."""
        issues = []

        for node in ast.walk(tree):
            # Check for match statements (Python 3.10+)
            if hasattr(ast, "Match") and isinstance(node, ast.Match):
                issues.append(
                    {
                        "type": "match_statement",
                        "severity": "critical",
                        "message": "Match statement requires Python 3.10+",
                        "line": getattr(node, "lineno", "unknown"),
                    }
                )

        return issues

    def _check_text_compatibility(self, code: str) -> list[dict[str, Any]]:
        """Check code text for compatibility issues."""
        issues = []

        # Check for PEP 604 union syntax (type | None)
        pep604_pattern = r"\w+\s*\|\s*\w+"
        if re.search(pep604_pattern, code):
            issues.append(
                {
                    "type": "pep604_union",
                    "severity": "critical",
                    "message": "PEP 604 union syntax (type | None) requires Python 3.10+",
                    "pattern": pep604_pattern,
                }
            )

        return issues


# Strategies for generating test data
@st.composite
def python_code_strategy(draw):
    """Generate Python code samples with potential compatibility issues."""

    # Base valid Python code
    base_codes = [
        "def simple_function():\n    return 42",
        "class SimpleClass:\n    def __init__(self):\n        self.value = 1",
        "import os\nfrom typing import Optional\n\ndef func(x: Optional[str]) -> int:\n    return len(x) if x else 0",
    ]

    base_code = draw(st.sampled_from(base_codes))

    # Potentially add compatibility issues
    add_issues = draw(st.booleans())

    if add_issues:
        issue_type = draw(st.sampled_from(["pep604_union", "match_statement"]))

        if issue_type == "pep604_union":
            # Add PEP 604 union syntax
            base_code += "\n\ndef bad_function(x: str | None) -> int | None:\n    return len(x) if x else None"

        elif issue_type == "match_statement":
            # Add match statement (Python 3.10+)
            base_code += "\n\ndef bad_match(value):\n    match value:\n        case 1:\n            return 'one'\n        case _:\n            return 'other'"

    return {
        "code": base_code,
        "has_compatibility_issues": add_issues,
        "expected_compatible": not add_issues,
    }


class TestPythonCompatibilityValidation:
    """Property-based tests for Python compatibility validation."""

    def setup_method(self):
        """Set up a fresh validator for each test."""
        self.validator = PythonCompatibilityValidator()

    @given(python_code_strategy())
    @settings(max_examples=30, deadline=3000)
    def test_compatibility_detection_accuracy(self, code_sample):
        """
        Property: Compatibility validation should accurately detect issues.
        **Feature: ai-agent-documentation, Property 6: Python Compatibility Validation**
        """
        result = self.validator.validate_code(code_sample["code"])

        # Verify result structure
        assert isinstance(result["is_compatible"], bool)
        assert isinstance(result["issues"], list)
        assert isinstance(result["total_issues"], int)

        # If we expect compatibility issues, validation should find them
        if code_sample["has_compatibility_issues"]:
            assert not result["is_compatible"] or result["total_issues"] > 0

    def test_pep604_union_detection(self):
        """
        Property: PEP 604 union syntax should be detected as incompatible.
        **Feature: ai-agent-documentation, Property 6: Python Compatibility Validation**
        """
        # Test various PEP 604 union patterns
        incompatible_codes = [
            "def func(x: str | None) -> int | None: pass",
            "def func(x: int | float) -> str | bytes: pass",
        ]

        for code in incompatible_codes:
            result = self.validator.validate_code(code)

            # Should detect PEP 604 union issue
            pep604_issues = [i for i in result["issues"] if i["type"] == "pep604_union"]
            assert len(pep604_issues) > 0, f"Failed to detect PEP 604 union in: {code}"
            assert not result["is_compatible"]

    def test_compatible_code_passes(self):
        """
        Property: Compatible code should pass validation.
        **Feature: ai-agent-documentation, Property 6: Python Compatibility Validation**
        """
        compatible_codes = [
            "from typing import Optional\n\ndef func(x: Optional[str]) -> Optional[int]: pass",
            "import os\nfrom pathlib import Path\n\ndef process_file(path: str) -> bool: return True",
            "class MyClass:\n    def __init__(self):\n        self.value = 42",
        ]

        for code in compatible_codes:
            result = self.validator.validate_code(code)

            # Should pass validation (no critical issues)
            critical_issues = [
                i for i in result["issues"] if i.get("severity") == "critical"
            ]
            assert (
                len(critical_issues) == 0
            ), f"Compatible code failed validation: {code}"

    @given(st.lists(python_code_strategy(), min_size=1, max_size=5))
    @settings(max_examples=20, deadline=2000)
    def test_validation_determinism(self, code_samples):
        """
        Property: Validation should be deterministic for the same input.
        **Feature: ai-agent-documentation, Property 6: Python Compatibility Validation**
        """
        for code_sample in code_samples:
            code = code_sample["code"]

            # Run validation multiple times
            result1 = self.validator.validate_code(code)
            result2 = self.validator.validate_code(code)

            # Results should be identical
            assert result1["is_compatible"] == result2["is_compatible"]
            assert result1["total_issues"] == result2["total_issues"]


if __name__ == "__main__":
    # Run the property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
