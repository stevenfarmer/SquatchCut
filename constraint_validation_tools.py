"""
Constraint Validation Tools for SquatchCut AI Agent Documentation Enhancement

This module provides practical tools for validating constraint compliance
in SquatchCut code changes and AI agent tasks.
"""

import ast
import os
import re
from typing import Any

from constraint_framework import ConstraintArea, constraint_framework


class CodeAnalyzer:
    """Analyzes Python code for constraint compliance."""

    def __init__(self):
        self.framework = constraint_framework

    def analyze_file(self, file_path: str) -> dict[str, Any]:
        """
        Analyze a Python file for constraint violations.

        Args:
            file_path: Path to the Python file to analyze

        Returns:
            Dictionary containing analysis results
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content, filename=file_path)

            # Analyze for various constraint violations
            violations = []

            # Check Python compatibility constraints
            violations.extend(self._check_python_compatibility(content, tree))

            # Check import patterns
            violations.extend(self._check_import_patterns(tree))

            # Check hydration patterns (if GUI file)
            if self._is_gui_file(file_path):
                violations.extend(self._check_hydration_patterns(content, tree))

            # Check measurement system patterns
            violations.extend(self._check_measurement_patterns(content))

            # Check export patterns
            if self._is_export_related(file_path, content):
                violations.extend(self._check_export_patterns(content))

            return {
                "file_path": file_path,
                "violations": violations,
                "total_violations": len(violations),
                "critical_violations": len(
                    [v for v in violations if v["severity"] == "CRITICAL"]
                ),
            }

        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}

    def _check_python_compatibility(
        self, content: str, tree: ast.AST
    ) -> list[dict[str, Any]]:
        """Check for Python version compatibility issues."""
        violations = []

        # Check for PEP 604 union syntax (type | None)
        if re.search(r"\w+\s*\|\s*None", content):
            violations.append(
                {
                    "constraint_id": "PYTHON-001",
                    "severity": "CRITICAL",
                    "message": "PEP 604 union syntax detected (type | None). Use Optional[type] instead.",
                    "line_pattern": r"\w+\s*\|\s*None",
                }
            )

        # Check for match statements (Python 3.10+)
        for node in ast.walk(tree):
            if hasattr(ast, "Match") and isinstance(node, ast.Match):
                violations.append(
                    {
                        "constraint_id": "PYTHON-001",
                        "severity": "CRITICAL",
                        "message": "Match statement detected. Not compatible with Python < 3.10.",
                        "line": getattr(node, "lineno", "unknown"),
                    }
                )

        return violations

    def _check_import_patterns(self, tree: ast.AST) -> list[dict[str, Any]]:
        """Check for relative import violations."""
        violations = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level > 0:
                violations.append(
                    {
                        "constraint_id": "PYTHON-002",
                        "severity": "CRITICAL",
                        "message": f"Relative import detected: {node.module}. Use absolute imports.",
                        "line": getattr(node, "lineno", "unknown"),
                    }
                )

        return violations

    def _check_hydration_patterns(
        self, content: str, tree: ast.AST
    ) -> list[dict[str, Any]]:
        """Check for hydration order violations in GUI files."""
        violations = []

        # Look for TaskPanel classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and "TaskPanel" in node.name:
                # Check for proper hydration order in __init__ or similar methods
                for method in node.body:
                    if isinstance(method, ast.FunctionDef) and method.name in [
                        "__init__",
                        "create",
                        "setup",
                    ]:
                        violations.extend(
                            self._check_method_hydration_order(method, content)
                        )

        # Check for preset auto-selection
        if re.search(
            r"preset.*setCurrentText.*(?!None|Custom)", content, re.IGNORECASE
        ):
            violations.append(
                {
                    "constraint_id": "HYDRATION-003",
                    "severity": "CRITICAL",
                    "message": "Possible preset auto-selection detected. Presets must start as 'None/Custom'.",
                    "line_pattern": r"preset.*setCurrentText",
                }
            )

        return violations

    def _check_method_hydration_order(
        self, method: ast.FunctionDef, content: str
    ) -> list[dict[str, Any]]:
        """Check hydration order within a method."""
        violations = []

        # Extract method source
        method_lines = content.split("\n")[
            method.lineno
            - 1 : (
                method.end_lineno
                if hasattr(method, "end_lineno")
                else method.lineno + 20
            )
        ]
        method_content = "\n".join(method_lines)

        # Look for widget creation before hydration
        hydrate_pattern = r"hydrate_from_params"
        widget_patterns = [
            r"create.*widget",
            r"\.addWidget",
            r"QWidget",
            r"QLabel",
            r"QLineEdit",
            r"QComboBox",
        ]

        hydrate_pos = -1
        widget_pos = float("inf")

        for i, line in enumerate(method_lines):
            if re.search(hydrate_pattern, line, re.IGNORECASE):
                hydrate_pos = i

            for pattern in widget_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    widget_pos = min(widget_pos, i)

        if hydrate_pos > 0 and widget_pos < hydrate_pos:
            violations.append(
                {
                    "constraint_id": "HYDRATION-001",
                    "severity": "CRITICAL",
                    "message": "Widget creation detected before hydrate_from_params() call.",
                    "line": method.lineno + widget_pos,
                }
            )

        return violations

    def _check_measurement_patterns(self, content: str) -> list[dict[str, Any]]:
        """Check for measurement system violations."""
        violations = []

        # Check for imperial storage (common mistake)
        if re.search(
            r"(width|height|size).*=.*\d+\.\d+.*(?:in|inch)", content, re.IGNORECASE
        ):
            violations.append(
                {
                    "constraint_id": "MEASUREMENT-001",
                    "severity": "CRITICAL",
                    "message": "Possible imperial unit storage detected. Internal storage must use millimeters.",
                    "line_pattern": r"(width|height|size).*=.*\d+\.\d+.*(?:in|inch)",
                }
            )

        # Check for decimal inch display
        if re.search(r"\.2f.*in(?:ch)?", content):
            violations.append(
                {
                    "constraint_id": "MEASUREMENT-002",
                    "severity": "CRITICAL",
                    "message": "Decimal inch display detected. Imperial UI must use fractional inches only.",
                    "line_pattern": r"\.2f.*in(?:ch)?",
                }
            )

        return violations

    def _check_export_patterns(self, content: str) -> list[dict[str, Any]]:
        """Check for export architecture violations."""
        violations = []

        # Check for direct FreeCAD geometry access in export context
        freecad_patterns = [
            r"FreeCAD\.ActiveDocument\.getObjects",
            r"\.getObjectsByLabel.*SquatchCut",
            r"\.Shape\.",
            r"\.Placement\.",
        ]

        export_context = re.search(r"(export|csv|svg|dxf)", content, re.IGNORECASE)

        if export_context:
            for pattern in freecad_patterns:
                if re.search(pattern, content):
                    violations.append(
                        {
                            "constraint_id": "EXPORT-002",
                            "severity": "CRITICAL",
                            "message": "Direct FreeCAD geometry access in export context. Use ExportJob data model.",
                            "line_pattern": pattern,
                        }
                    )

        # Check for export functions outside exporter.py
        if "exporter.py" not in content and re.search(r"def.*export.*\(", content):
            violations.append(
                {
                    "constraint_id": "EXPORT-001",
                    "severity": "CRITICAL",
                    "message": "Export function defined outside exporter.py. All exports must go through core/exporter.py.",
                    "line_pattern": r"def.*export.*\(",
                }
            )

        return violations

    def _is_gui_file(self, file_path: str) -> bool:
        """Check if file is a GUI-related file."""
        return any(
            indicator in file_path.lower()
            for indicator in ["gui/", "taskpanel", "dialog", "widget"]
        )

    def _is_export_related(self, file_path: str, content: str) -> bool:
        """Check if file is export-related."""
        return "export" in file_path.lower() or any(
            keyword in content.lower() for keyword in ["export", "csv", "svg", "dxf"]
        )


class TaskSpecificationValidator:
    """Validates AI agent task specifications for constraint compliance."""

    def __init__(self):
        self.framework = constraint_framework

    def validate_task_specification(self, task_spec: dict[str, Any]) -> dict[str, Any]:
        """
        Validate a task specification for completeness and constraint awareness.

        Args:
            task_spec: Dictionary containing task specification details

        Returns:
            Validation result with compliance status and recommendations
        """
        violations = []
        warnings = []
        recommendations = []

        # Check required fields
        required_fields = [
            "reasoning_level",
            "context",
            "requirements",
            "file_paths",
            "acceptance_criteria",
        ]
        for field in required_fields:
            if field not in task_spec or not task_spec[field]:
                violations.append(f"Missing required field: {field}")

        # Validate reasoning level
        if "reasoning_level" in task_spec:
            valid_levels = ["LOW", "MEDIUM", "HIGH", "EXTRA-HIGH"]
            if task_spec["reasoning_level"] not in valid_levels:
                violations.append(
                    f"Invalid reasoning level: {task_spec['reasoning_level']}"
                )

        # Check constraint awareness
        if "file_paths" in task_spec:
            relevant_constraints = self._get_relevant_constraints(
                task_spec["file_paths"]
            )

            # Check if constraints are mentioned in requirements or acceptance criteria
            constraint_mentions = self._check_constraint_mentions(
                task_spec, relevant_constraints
            )

            if not constraint_mentions and relevant_constraints:
                warnings.append(
                    "Task specification does not mention relevant constraints"
                )
                recommendations.extend(
                    [
                        f"Consider constraint {c.id}: {c.rule}"
                        for c in relevant_constraints[:3]  # Top 3 most relevant
                    ]
                )

        # Check acceptance criteria quality
        if "acceptance_criteria" in task_spec:
            criteria_quality = self._assess_acceptance_criteria(
                task_spec["acceptance_criteria"]
            )
            warnings.extend(criteria_quality["warnings"])
            recommendations.extend(criteria_quality["recommendations"])

        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "recommendations": recommendations,
            "constraint_compliance_score": self._calculate_compliance_score(task_spec),
        }

    def _get_relevant_constraints(self, file_paths: list[str]) -> list:
        """Get constraints relevant to the specified file paths."""
        relevant_areas = set()

        for file_path in file_paths:
            if "gui/" in file_path or "taskpanel" in file_path.lower():
                relevant_areas.update([ConstraintArea.UI, ConstraintArea.HYDRATION])
            if "core/" in file_path:
                relevant_areas.update(
                    [ConstraintArea.MEASUREMENT, ConstraintArea.EXPORT]
                )
            if "test" in file_path.lower():
                relevant_areas.add(ConstraintArea.TESTING)
            if file_path.endswith(".py"):
                relevant_areas.add(ConstraintArea.PYTHON)

        relevant_constraints = []
        for area in relevant_areas:
            relevant_constraints.extend(self.framework.get_constraints_by_area(area))

        # Prioritize critical constraints
        relevant_constraints.sort(key=lambda c: (c.severity.value, c.id))

        return relevant_constraints

    def _check_constraint_mentions(
        self, task_spec: dict[str, Any], constraints: list
    ) -> bool:
        """Check if task specification mentions relevant constraints."""
        text_fields = ["context", "requirements", "acceptance_criteria"]
        combined_text = " ".join(
            str(task_spec.get(field, "")) for field in text_fields
        ).lower()

        constraint_keywords = [
            "hydration",
            "hydrate_from_params",
            "millimeter",
            "fractional",
            "exporter.py",
            "exportjob",
            "python 3.10",
            "relative import",
            "settings panel",
        ]

        return any(keyword in combined_text for keyword in constraint_keywords)

    def _assess_acceptance_criteria(self, criteria: Any) -> dict[str, list[str]]:
        """Assess the quality of acceptance criteria."""
        warnings = []
        recommendations = []

        if isinstance(criteria, str):
            criteria = [criteria]

        if not criteria or len(criteria) == 0:
            warnings.append("No acceptance criteria specified")
            return {"warnings": warnings, "recommendations": recommendations}

        for criterion in criteria:
            if len(criterion) < 20:
                warnings.append("Acceptance criteria may be too brief")

            if not any(
                word in criterion.lower()
                for word in ["must", "should", "shall", "will"]
            ):
                recommendations.append(
                    "Consider using stronger requirement language (must, shall)"
                )

            if "test" not in criterion.lower() and "verify" not in criterion.lower():
                recommendations.append(
                    "Consider adding verification/testing requirements"
                )

        return {"warnings": warnings, "recommendations": recommendations}

    def _calculate_compliance_score(self, task_spec: dict[str, Any]) -> float:
        """Calculate a compliance score (0-100) for the task specification."""
        score = 100.0

        # Deduct for missing required fields
        required_fields = [
            "reasoning_level",
            "context",
            "requirements",
            "file_paths",
            "acceptance_criteria",
        ]
        missing_fields = sum(
            1
            for field in required_fields
            if field not in task_spec or not task_spec[field]
        )
        score -= missing_fields * 20

        # Deduct for poor acceptance criteria
        if "acceptance_criteria" in task_spec:
            criteria = task_spec["acceptance_criteria"]
            if isinstance(criteria, str):
                criteria = [criteria]

            if len(criteria) < 2:
                score -= 10

            avg_length = (
                sum(len(c) for c in criteria) / len(criteria) if criteria else 0
            )
            if avg_length < 30:
                score -= 10

        # Bonus for constraint awareness
        if "file_paths" in task_spec:
            relevant_constraints = self._get_relevant_constraints(
                task_spec["file_paths"]
            )
            if self._check_constraint_mentions(task_spec, relevant_constraints):
                score += 10

        return max(0.0, min(100.0, score))


class ConstraintChecker:
    """Utility for checking constraint compliance across multiple files."""

    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.validator = TaskSpecificationValidator()

    def check_project_compliance(self, project_root: str) -> dict[str, Any]:
        """
        Check constraint compliance across an entire project.

        Args:
            project_root: Root directory of the project

        Returns:
            Comprehensive compliance report
        """
        python_files = []

        # Find all Python files
        for root, dirs, files in os.walk(project_root):
            # Skip common non-source directories
            dirs[:] = [
                d
                for d in dirs
                if d not in [".git", "__pycache__", ".pytest_cache", "node_modules"]
            ]

            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))

        # Analyze each file
        file_results = []
        total_violations = 0
        critical_violations = 0

        for file_path in python_files:
            result = self.analyzer.analyze_file(file_path)
            if "error" not in result:
                file_results.append(result)
                total_violations += result["total_violations"]
                critical_violations += result["critical_violations"]

        # Generate summary
        return {
            "project_root": project_root,
            "files_analyzed": len(file_results),
            "total_violations": total_violations,
            "critical_violations": critical_violations,
            "compliance_score": self._calculate_project_score(file_results),
            "file_results": file_results,
            "top_violations": self._get_top_violations(file_results),
        }

    def _calculate_project_score(self, file_results: list[dict[str, Any]]) -> float:
        """Calculate overall project compliance score."""
        if not file_results:
            return 100.0

        total_files = len(file_results)
        files_with_violations = sum(
            1 for r in file_results if r["total_violations"] > 0
        )
        critical_files = sum(1 for r in file_results if r["critical_violations"] > 0)

        # Base score starts at 100
        score = 100.0

        # Deduct for files with violations
        violation_penalty = (files_with_violations / total_files) * 50
        score -= violation_penalty

        # Additional penalty for critical violations
        critical_penalty = (critical_files / total_files) * 30
        score -= critical_penalty

        return max(0.0, score)

    def _get_top_violations(
        self, file_results: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Get the most common violations across the project."""
        violation_counts = {}

        for result in file_results:
            for violation in result.get("violations", []):
                constraint_id = violation["constraint_id"]
                if constraint_id not in violation_counts:
                    violation_counts[constraint_id] = {
                        "constraint_id": constraint_id,
                        "severity": violation["severity"],
                        "count": 0,
                        "files": [],
                    }
                violation_counts[constraint_id]["count"] += 1
                violation_counts[constraint_id]["files"].append(result["file_path"])

        # Sort by count and severity
        top_violations = sorted(
            violation_counts.values(),
            key=lambda x: (x["severity"] == "CRITICAL", x["count"]),
            reverse=True,
        )

        return top_violations[:10]  # Top 10 violations


# Utility functions for easy access
def check_file_compliance(file_path: str) -> dict[str, Any]:
    """Quick function to check a single file's compliance."""
    analyzer = CodeAnalyzer()
    return analyzer.analyze_file(file_path)


def validate_task_spec(task_spec: dict[str, Any]) -> dict[str, Any]:
    """Quick function to validate a task specification."""
    validator = TaskSpecificationValidator()
    return validator.validate_task_specification(task_spec)


def generate_constraint_checklist(
    task_type: str, file_paths: list[str] = None
) -> list[str]:
    """Quick function to generate a constraint checklist."""
    return constraint_framework.generate_constraint_checklist(task_type, file_paths)


if __name__ == "__main__":
    # Example usage
    checker = ConstraintChecker()

    # Check a single file
    result = check_file_compliance("example_file.py")
    print("File compliance result:", result)

    # Validate a task specification
    task_spec = {
        "reasoning_level": "HIGH",
        "context": "Implement new TaskPanel for settings",
        "requirements": ["Create settings UI", "Handle hydration"],
        "file_paths": ["freecad/SquatchCut/gui/taskpanel_settings.py"],
        "acceptance_criteria": [
            "Settings panel must open",
            "Hydration must occur before widget creation",
        ],
    }

    validation_result = validate_task_spec(task_spec)
    print("Task specification validation:", validation_result)

    # Generate constraint checklist
    checklist = generate_constraint_checklist(
        "ui", ["freecad/SquatchCut/gui/taskpanel_main.py"]
    )
    print("Constraint checklist:")
    for item in checklist:
        print(f"  {item}")
