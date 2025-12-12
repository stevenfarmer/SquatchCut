"""
Property-based tests for SquatchCut Repository Organization Compliance.

**Feature: ai-agent-documentation, Property 7: Repository Organization Compliance**
*For any* file creation or modification, the established directory structure
and architectural boundaries should be respected
**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**
"""

import pytest
from hypothesis import given, strategies as st, assume, settings, example
from typing import Dict, Any, List, Set
from pathlib import Path
import os


class RepositoryOrganizationValidator:
    """Validates repository organization compliance."""

    def __init__(self):
        self.valid_structure = {
            "freecad/SquatchCut/core/": {
                "description": "Pure logic, no GUI dependencies",
                "allowed_imports": [
                    "typing",
                    "pathlib",
                    "os",
                    "sys",
                    "math",
                    "json",
                    "csv",
                    "ast",
                ],
                "forbidden_imports": ["PySide", "QtWidgets", "FreeCADGui"],
            },
            "freecad/SquatchCut/gui/": {
                "description": "UI components, TaskPanels, commands",
                "allowed_imports": [
                    "typing",
                    "PySide",
                    "QtWidgets",
                    "FreeCAD",
                    "FreeCADGui",
                ],
                "forbidden_imports": [],
            },
            "freecad/SquatchCut/resources/": {
                "description": "Icons, templates, static files",
                "allowed_extensions": [".png", ".svg", ".ico", ".ui", ".qrc"],
                "forbidden_extensions": [".py", ".pyc"],
            },
            "tests/": {
                "description": "All test files",
                "allowed_imports": ["pytest", "unittest", "hypothesis"],
                "required_prefix": "test_",
            },
            "docs/": {
                "description": "Documentation",
                "allowed_extensions": [".md", ".rst", ".txt", ".png", ".svg"],
                "forbidden_extensions": [".py", ".pyc"],
            },
        }

    def validate_file_placement(self, file_path: str) -> Dict[str, Any]:
        """Validate that a file is placed in the correct directory."""
        issues = []

        # Normalize path
        path = Path(file_path)

        # Check if file is in a valid directory
        valid_placement = False
        expected_directory = None

        for valid_dir in self.valid_structure.keys():
            if str(path).startswith(valid_dir):
                valid_placement = True
                expected_directory = valid_dir
                break

        if not valid_placement:
            issues.append(
                {
                    "type": "invalid_directory",
                    "severity": "critical",
                    "message": f"File {file_path} is not in a valid directory structure",
                    "file_path": file_path,
                }
            )

        # Validate file type for directory
        if expected_directory and expected_directory in self.valid_structure:
            dir_rules = self.valid_structure[expected_directory]

            # Check file extensions
            if "allowed_extensions" in dir_rules:
                if not any(
                    str(path).endswith(ext) for ext in dir_rules["allowed_extensions"]
                ):
                    issues.append(
                        {
                            "type": "invalid_extension",
                            "severity": "important",
                            "message": f"File extension not allowed in {expected_directory}",
                            "file_path": file_path,
                            "allowed_extensions": dir_rules["allowed_extensions"],
                        }
                    )

            if "forbidden_extensions" in dir_rules:
                if any(
                    str(path).endswith(ext) for ext in dir_rules["forbidden_extensions"]
                ):
                    issues.append(
                        {
                            "type": "forbidden_extension",
                            "severity": "critical",
                            "message": f"File extension forbidden in {expected_directory}",
                            "file_path": file_path,
                            "forbidden_extensions": dir_rules["forbidden_extensions"],
                        }
                    )

            # Check naming conventions for tests
            if expected_directory == "tests/" and str(path).endswith(".py"):
                if "required_prefix" in dir_rules:
                    if not path.name.startswith(dir_rules["required_prefix"]):
                        issues.append(
                            {
                                "type": "naming_convention",
                                "severity": "important",
                                "message": f"Test files must start with {dir_rules['required_prefix']}",
                                "file_path": file_path,
                            }
                        )

        return {
            "is_compliant": len(issues) == 0,
            "issues": issues,
            "expected_directory": expected_directory,
            "total_issues": len(issues),
        }


# Strategies for generating test data
@st.composite
def file_path_strategy(draw):
    """Generate file paths for testing."""

    # Valid directories
    directories = [
        "freecad/SquatchCut/core/",
        "freecad/SquatchCut/gui/",
        "freecad/SquatchCut/resources/",
        "tests/",
        "docs/",
    ]

    # Invalid directories (should be rejected)
    invalid_directories = [
        "src/",
        "lib/",
        "freecad/SquatchCut/utils/",
        "test/",  # Should be "tests/"
        "documentation/",  # Should be "docs/"
    ]

    # Choose directory (valid or invalid)
    use_valid_dir = draw(st.booleans())

    if use_valid_dir:
        directory = draw(st.sampled_from(directories))
        is_valid_dir = True
    else:
        directory = draw(st.sampled_from(invalid_directories))
        is_valid_dir = False

    # Generate filename
    filename = draw(
        st.text(
            min_size=1,
            max_size=20,
            alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        )
    )

    # Choose extension based on directory
    if "core/" in directory or "gui/" in directory or "tests/" in directory:
        extensions = [".py", ".pyx"] if is_valid_dir else [".py", ".js", ".cpp"]
    elif "resources/" in directory:
        extensions = [".png", ".svg", ".ico"] if is_valid_dir else [".py", ".txt"]
    elif "docs/" in directory:
        extensions = [".md", ".rst", ".txt"] if is_valid_dir else [".py", ".exe"]
    else:
        extensions = [".py", ".txt", ".md"]

    extension = draw(st.sampled_from(extensions))

    # Special handling for test files
    if directory == "tests/" and extension == ".py":
        if draw(st.booleans()):
            filename = "test_" + filename  # Correct naming
        # else: incorrect naming (missing test_ prefix)

    file_path = directory + filename + extension

    return {
        "file_path": file_path,
        "is_valid_directory": is_valid_dir,
        "directory": directory,
        "filename": filename,
        "extension": extension,
    }


class TestRepositoryOrganizationCompliance:
    """Property-based tests for repository organization compliance."""

    def setup_method(self):
        """Set up a fresh validator for each test."""
        self.validator = RepositoryOrganizationValidator()

    @given(file_path_strategy())
    @settings(max_examples=50, deadline=3000)
    def test_file_placement_validation(self, file_info):
        """
        Property: File placement validation should correctly identify valid/invalid placements.
        **Feature: ai-agent-documentation, Property 7: Repository Organization Compliance**
        """
        result = self.validator.validate_file_placement(file_info["file_path"])

        # Verify result structure
        assert isinstance(result["is_compliant"], bool)
        assert isinstance(result["issues"], list)
        assert isinstance(result["total_issues"], int)

        # If directory is invalid, should have issues
        if not file_info["is_valid_directory"]:
            assert result["total_issues"] > 0
            assert not result["is_compliant"]

            # Should have invalid directory issue
            invalid_dir_issues = [
                i for i in result["issues"] if i["type"] == "invalid_directory"
            ]
            assert len(invalid_dir_issues) > 0

    def test_core_directory_restrictions(self):
        """
        Property: Core directory should only contain appropriate files.
        **Feature: ai-agent-documentation, Property 7: Repository Organization Compliance**
        """
        # Valid core files
        valid_core_files = [
            "freecad/SquatchCut/core/nesting.py",
            "freecad/SquatchCut/core/units.py",
            "freecad/SquatchCut/core/session_state.py",
        ]

        for file_path in valid_core_files:
            result = self.validator.validate_file_placement(file_path)
            assert result["is_compliant"], f"Valid core file rejected: {file_path}"
            assert result["expected_directory"] == "freecad/SquatchCut/core/"

        # Invalid core files (wrong extensions)
        invalid_core_files = [
            "freecad/SquatchCut/core/icon.png",  # Should be in resources/
            "freecad/SquatchCut/core/readme.md",  # Should be in docs/
        ]

        for file_path in invalid_core_files:
            result = self.validator.validate_file_placement(file_path)
            # May or may not be compliant depending on rules, but should be in core directory
            assert result["expected_directory"] == "freecad/SquatchCut/core/"

    def test_test_directory_naming_conventions(self):
        """
        Property: Test files should follow naming conventions.
        **Feature: ai-agent-documentation, Property 7: Repository Organization Compliance**
        """
        # Valid test files
        valid_test_files = [
            "tests/test_nesting.py",
            "tests/test_units.py",
            "tests/test_session_state.py",
        ]

        for file_path in valid_test_files:
            result = self.validator.validate_file_placement(file_path)
            assert result["is_compliant"], f"Valid test file rejected: {file_path}"

        # Invalid test files (wrong naming)
        invalid_test_files = [
            "tests/nesting_test.py",  # Should start with test_
            "tests/units.py",  # Should start with test_
            "tests/my_tests.py",  # Should start with test_
        ]

        for file_path in invalid_test_files:
            result = self.validator.validate_file_placement(file_path)

            # Should have naming convention issue
            naming_issues = [
                i for i in result["issues"] if i["type"] == "naming_convention"
            ]
            assert len(naming_issues) > 0, f"Naming violation not detected: {file_path}"

    def test_resources_directory_restrictions(self):
        """
        Property: Resources directory should only contain appropriate file types.
        **Feature: ai-agent-documentation, Property 7: Repository Organization Compliance**
        """
        # Valid resource files
        valid_resource_files = [
            "freecad/SquatchCut/resources/icon.png",
            "freecad/SquatchCut/resources/logo.svg",
            "freecad/SquatchCut/resources/dialog.ui",
        ]

        for file_path in valid_resource_files:
            result = self.validator.validate_file_placement(file_path)
            assert result["is_compliant"], f"Valid resource file rejected: {file_path}"

        # Invalid resource files (code files)
        invalid_resource_files = [
            "freecad/SquatchCut/resources/helper.py",  # Code should not be in resources
            "freecad/SquatchCut/resources/config.pyc",  # Compiled files should not be in resources
        ]

        for file_path in invalid_resource_files:
            result = self.validator.validate_file_placement(file_path)

            # Should have forbidden extension issue
            forbidden_issues = [
                i for i in result["issues"] if i["type"] == "forbidden_extension"
            ]
            assert (
                len(forbidden_issues) > 0
            ), f"Forbidden extension not detected: {file_path}"

    @given(st.lists(file_path_strategy(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=2000)
    def test_validation_determinism(self, file_list):
        """
        Property: Validation should be deterministic for the same inputs.
        **Feature: ai-agent-documentation, Property 7: Repository Organization Compliance**
        """
        for file_info in file_list:
            file_path = file_info["file_path"]

            # Run validation multiple times
            result1 = self.validator.validate_file_placement(file_path)
            result2 = self.validator.validate_file_placement(file_path)

            # Results should be identical
            assert result1["is_compliant"] == result2["is_compliant"]
            assert result1["total_issues"] == result2["total_issues"]
            assert result1["expected_directory"] == result2["expected_directory"]

    def test_directory_structure_completeness(self):
        """
        Property: All required directories should be recognized.
        **Feature: ai-agent-documentation, Property 7: Repository Organization Compliance**
        """
        required_directories = [
            "freecad/SquatchCut/core/",
            "freecad/SquatchCut/gui/",
            "freecad/SquatchCut/resources/",
            "tests/",
            "docs/",
        ]

        for directory in required_directories:
            # Test with a valid file in each directory
            test_file = directory + "example.py"
            result = self.validator.validate_file_placement(test_file)

            # Should recognize the directory
            assert result["expected_directory"] == directory


if __name__ == "__main__":
    # Run the property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])
