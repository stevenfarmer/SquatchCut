"""
SquatchCut Constraint Framework

This module provides a structured system for defining, classifying, and enforcing
architectural constraints for AI agents working on the SquatchCut project.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Severity(Enum):
    """Constraint severity levels with clear enforcement expectations."""

    CRITICAL = "CRITICAL"  # Cannot be violated under any circumstances
    IMPORTANT = "IMPORTANT"  # Should not be violated without explicit approval
    RECOMMENDED = "RECOMMENDED"  # Best practices that improve maintainability


class ConstraintArea(Enum):
    """Categories of constraints for systematic organization."""

    HYDRATION = "HYDRATION"  # Initialization and state management patterns
    MEASUREMENT = "MEASUREMENT"  # Unit conversion and display patterns
    EXPORT = "EXPORT"  # Data export architecture and patterns
    UI = "UI"  # User interface behavior and patterns
    TESTING = "TESTING"  # Test requirements and patterns
    REPOSITORY = "REPOSITORY"  # File organization and structure
    PYTHON = "PYTHON"  # Language compatibility requirements
    COMMUNICATION = "COMMUNICATION"  # AI agent interaction protocols


@dataclass
class Constraint:
    """Definition of an architectural or behavioral requirement."""

    id: str
    area: ConstraintArea
    severity: Severity
    rule: str
    rationale: str
    examples: list[str]
    anti_patterns: list[str]
    validation_method: str | None = None
    source_documents: list[str] = None

    def __post_init__(self):
        if self.source_documents is None:
            self.source_documents = []


@dataclass
class ValidationResult:
    """Result of constraint validation."""

    is_compliant: bool
    violated_constraints: list[Constraint]
    warnings: list[str]
    recommendations: list[str]
    approval_required: bool


class ConstraintFramework:
    """
    Structured system for defining and enforcing architectural constraints.

    This framework provides:
    - Systematic constraint classification
    - Validation and enforcement mechanisms
    - Constraint checklist generation
    - Rationale and example provision
    """

    def __init__(self):
        self.constraints: dict[str, Constraint] = {}
        self._initialize_core_constraints()

    def define_constraint(
        self,
        constraint_id: str,
        area: ConstraintArea,
        severity: Severity,
        rule: str,
        rationale: str,
        examples: list[str] = None,
        anti_patterns: list[str] = None,
        validation_method: str = None,
        source_documents: list[str] = None,
    ) -> Constraint:
        """Define a new constraint in the framework."""
        constraint = Constraint(
            id=constraint_id,
            area=area,
            severity=severity,
            rule=rule,
            rationale=rationale,
            examples=examples or [],
            anti_patterns=anti_patterns or [],
            validation_method=validation_method,
            source_documents=source_documents or [],
        )

        self.constraints[constraint_id] = constraint
        return constraint

    def get_constraint(self, constraint_id: str) -> Constraint | None:
        """Retrieve a constraint by ID."""
        return self.constraints.get(constraint_id)

    def get_constraints_by_area(self, area: ConstraintArea) -> list[Constraint]:
        """Get all constraints for a specific area."""
        return [c for c in self.constraints.values() if c.area == area]

    def get_constraints_by_severity(self, severity: Severity) -> list[Constraint]:
        """Get all constraints oific severity level."""
        return [c for c in self.constraints.values() if c.severity == severity]

    def validate_compliance(self, code_change: dict[str, Any]) -> ValidationResult:
        """
        Validate compliance with constraints for a code change.

        Args:
            code_change: Dictionary containing information about the code change
                        (file paths, operation type, affected areas, etc.)

        Returns:
            ValidationResult with compliance status and recommendations
        """
        violated_constraints = []
        warnings = []
        recommendations = []

        # Determine which constraints apply based on the code change
        applicable_constraints = self._get_applicable_constraints(code_change)

        # Validate each applicable constraint
        for constraint in applicable_constraints:
            if not self._validate_constraint(constraint, code_change):
                violated_constraints.append(constraint)

        # Generate warnings and recommendations
        for constraint in applicable_constraints:
            if constraint.severity == Severity.RECOMMENDED:
                recommendations.append(f"Consider: {constraint.rule}")
            elif constraint.severity == Severity.IMPORTANT:
                warnings.append(f"Important: {constraint.rule}")

        # Determine if approval is required
        approval_required = any(
            c.severity == Severity.IMPORTANT for c in violated_constraints
        )

        return ValidationResult(
            is_compliant=len(violated_constraints) == 0,
            violated_constraints=violated_constraints,
            warnings=warnings,
            recommendations=recommendations,
            approval_required=approval_required,
        )

    def generate_constraint_checklist(
        self, task_type: str, file_paths: list[str] = None
    ) -> list[str]:
        """
        Generate a constraint checklist for a specific task type.

        Args:
            task_type: Type of task (e.g., "hydration", "ui", "export")
            file_paths: Optional list of file paths being modified

        Returns:
            List of constraint check items
        """
        checklist = []

        # Determine relevant constraint areas based on task type and file paths
        relevant_areas = self._determine_relevant_areas(task_type, file_paths)

        # Add critical constraints first
        critical_constraints = [
            c
            for c in self.constraints.values()
            if c.severity == Severity.CRITICAL and c.area in relevant_areas
        ]

        for constraint in critical_constraints:
            checklist.append(f"✓ CRITICAL: {constraint.rule}")
            if constraint.validation_method:
                checklist.append(f"  Validation: {constraint.validation_method}")

        # Add important constraints
        important_constraints = [
            c
            for c in self.constraints.values()
            if c.severity == Severity.IMPORTANT and c.area in relevant_areas
        ]

        for constraint in important_constraints:
            checklist.append(f"⚠ IMPORTANT: {constraint.rule}")
            if constraint.validation_method:
                checklist.append(f"  Validation: {constraint.validation_method}")

        return checklist

    def provide_constraint_rationale(self, constraint_id: str) -> str | None:
        """Provide detailed rationale for a specific constraint."""
        constraint = self.get_constraint(constraint_id)
        if not constraint:
            return None

        rationale = f"Constraint: {constraint.rule}\n\n"
        rationale += f"Rationale: {constraint.rationale}\n\n"

        if constraint.examples:
            rationale += "Examples:\n"
            for example in constraint.examples:
                rationale += f"  - {example}\n"
            rationale += "\n"

        if constraint.anti_patterns:
            rationale += "Anti-patterns to avoid:\n"
            for anti_pattern in constraint.anti_patterns:
                rationale += f"  - {anti_pattern}\n"
            rationale += "\n"

        if constraint.validation_method:
            rationale += f"Validation: {constraint.validation_method}\n"

        return rationale

    def _initialize_core_constraints(self):
        """Initialize the core SquatchCut constraints from the analysis."""

        # CRITICAL Hydration Constraints
        self.define_constraint(
            "HYDRATION-001",
            ConstraintArea.HYDRATION,
            Severity.CRITICAL,
            "hydrate_from_params() MUST be called before creating UI widgets",
            "Ensures consistent state initialization and prevents UI/data mismatches",
            examples=[
                "def create_taskpanel(self): self.hydrate_from_params(); self.create_widgets()",
                "Load session_state → Call hydrate_from_params() → Create widgets → Populate values",
            ],
            anti_patterns=[
                "Creating widgets before hydration",
                "Accessing GUI modules from hydration functions",
                "Modifying defaults during hydration",
            ],
            validation_method="Check TaskPanel initialization order in all UI code",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        self.define_constraint(
            "HYDRATION-002",
            ConstraintArea.HYDRATION,
            Severity.CRITICAL,
            "Defaults MUST only change via Settings panel save operations",
            "Prevents accidental default modifications and maintains user expectations",
            examples=[
                "Only Settings.save() can modify stored defaults",
                "TaskPanel load never modifies defaults",
            ],
            anti_patterns=[
                "Modifying defaults during TaskPanel initialization",
                "Changing defaults when presets are selected",
            ],
            validation_method="Verify no default modifications outside Settings save flow",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        self.define_constraint(
            "HYDRATION-003",
            ConstraintArea.HYDRATION,
            Severity.CRITICAL,
            "Presets MUST NEVER be auto-selected on panel load",
            "Maintains clear separation between defaults and presets",
            examples=[
                "self.preset_combo.setCurrentText('None / Custom')  # Always start with None"
            ],
            anti_patterns=[
                "Auto-selecting presets based on current sheet size",
                "Inferring presets from loaded defaults",
            ],
            validation_method="Check that preset selection always starts as 'None/Custom'",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        # CRITICAL Measurement Constraints
        self.define_constraint(
            "MEASUREMENT-001",
            ConstraintArea.MEASUREMENT,
            Severity.CRITICAL,
            "Internal storage MUST always use millimeters",
            "Ensures consistent calculations and prevents conversion errors",
            examples=[
                "internal_width = inches_to_mm(48.0)  # Always store mm internally",
                "All calculations performed in mm units",
            ],
            anti_patterns=[
                "Storing imperial values internally",
                "Mixed unit calculations",
            ],
            validation_method="Verify all internal calculations use mm units",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        self.define_constraint(
            "MEASUREMENT-002",
            ConstraintArea.MEASUREMENT,
            Severity.CRITICAL,
            "Imperial UI MUST use fractional inches only (no decimals)",
            "Matches woodworking industry standards and user expectations",
            examples=[
                "display_text = format_fractional_inches(mm_to_inches(width))",
                "Support formats: '48', '3/4', '48 3/4', '48-3/4'",
            ],
            anti_patterns=[
                "Using decimal inches in UI display",
                "Inconsistent fractional formatting",
            ],
            validation_method="Check all imperial display formatting uses fractions",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        # CRITICAL Export Constraints
        self.define_constraint(
            "EXPORT-001",
            ConstraintArea.EXPORT,
            Severity.CRITICAL,
            "All exports MUST go through freecad/SquatchCut/core/exporter.py",
            "Ensures consistent export behavior and data integrity",
            examples=[
                "export_job = build_export_job_from_current_nesting()",
                "export_cutlist(export_job, file_path)",
            ],
            anti_patterns=[
                "Direct FreeCAD geometry access for exports",
                "Custom export functions outside exporter.py",
            ],
            validation_method="Verify no direct export implementations outside exporter.py",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        self.define_constraint(
            "EXPORT-002",
            ConstraintArea.EXPORT,
            Severity.CRITICAL,
            "ExportJob/ExportSheet/ExportPartPlacement MUST be the only sources of truth for export geometry",
            "Prevents inconsistencies between FreeCAD geometry and export data",
            examples=[
                "Use ExportJob data for all export operations",
                "Never read FreeCAD document objects when ExportJob exists",
            ],
            anti_patterns=[
                "Reading FreeCAD geometry directly for exports",
                "Bypassing ExportJob data model",
            ],
            validation_method="Check that exports never derive from FreeCAD document objects when ExportJob exists",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        # CRITICAL Python Constraints
        self.define_constraint(
            "PYTHON-001",
            ConstraintArea.PYTHON,
            Severity.CRITICAL,
            "Code MUST be compatible with Python versions older than 3.10",
            "FreeCAD compatibility requirements",
            examples=[
                "Use Optional[type] instead of type | None",
                "Avoid match statements and other 3.10+ features",
            ],
            anti_patterns=[
                "Using PEP 604 type unions (type | None)",
                "Using Python 3.10+ exclusive features",
            ],
            validation_method="Check for PEP 604 unions and other modern Python features",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        self.define_constraint(
            "PYTHON-002",
            ConstraintArea.PYTHON,
            Severity.CRITICAL,
            "No relative imports, especially in FreeCAD integration code",
            "FreeCAD module loading compatibility",
            examples=[
                "from SquatchCut.core import nesting  # Absolute import",
                "import FreeCAD  # Direct import",
            ],
            anti_patterns=[
                "from .core import nesting  # Relative import",
                "from ..gui import commands  # Relative import",
            ],
            validation_method="Scan for relative import statements",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        # CRITICAL UI Constraints
        self.define_constraint(
            "UI-001",
            ConstraintArea.UI,
            Severity.CRITICAL,
            "Settings panel MUST always open successfully",
            "Critical for user configuration and system functionality",
            examples=[
                "Settings panel opens under all conditions",
                "Proper error handling for Settings initialization",
            ],
            anti_patterns=[
                "Settings panel failing to open",
                "Unhandled Settings initialization errors",
            ],
            validation_method="Test Settings panel opening under all conditions",
            source_documents=["AGENTS.md", "Project_Guide_v3.3.md"],
        )

        # CRITICAL Communication and Collaboration Constraints
        self.define_constraint(
            "COMMUNICATION-001",
            ConstraintArea.COMMUNICATION,
            Severity.CRITICAL,
            "Treat the user as a non-technical stakeholder and communicate as Lead Developer & Product Manager in plain English first",
            "Ensures stakeholder-ready communication and avoids jargon-first responses",
            examples=[
                "Begin responses with a brief plain-English plan before technical details",
                "Reference constraints and risks in simple language the user can confirm",
            ],
            anti_patterns=[
                "Assuming technical expertise from the user",
                "Diving into implementation without a plain-English outline",
            ],
            validation_method="Check AGENTS.md/AI_AGENT_HANDBOOK.md for Lead Developer & Product Manager framing",
            source_documents=["AGENTS.md", "AI_AGENT_HANDBOOK.md"],
        )

        self.define_constraint(
            "COMMUNICATION-002",
            ConstraintArea.COMMUNICATION,
            Severity.CRITICAL,
            "Apply the discovery process (pause, ask 3-4 clarifying questions, validate, propose) before coding vague requests",
            "Prevents misalignment and reduces rework when requirements are incomplete",
            examples=[
                "Pause -> Ask clarifying questions -> Restate goal -> Propose plan",
                "Confirm acceptance criteria and tests before editing files",
            ],
            anti_patterns=[
                "Starting implementation without clarifying scope",
                "Skipping plan confirmation for ambiguous asks",
            ],
            validation_method="Verify discovery steps are documented and followed before coding",
            source_documents=["AGENTS.md", "AI_AGENT_HANDBOOK.md"],
        )

        self.define_constraint(
            "COMMUNICATION-003",
            ConstraintArea.COMMUNICATION,
            Severity.CRITICAL,
            "Escalate ambiguous or conflicting instructions before implementation",
            "Avoids constraint violations and misaligned work when guidance is unclear",
            examples=[
                "Stop and ask for guidance when requirements conflict or are incomplete",
                "Document constraint risks in the plan before proceeding",
            ],
            anti_patterns=[
                "Guessing user intent when instructions conflict",
                "Proceeding despite missing acceptance criteria",
            ],
            validation_method="Check escalation triggers are documented and used during planning",
            source_documents=["AGENTS.md", "AI_AGENT_HANDBOOK.md"],
        )

        self.define_constraint(
            "COMMUNICATION-004",
            ConstraintArea.COMMUNICATION,
            Severity.IMPORTANT,
            "Enforce branch isolation with naming ai/<worker-name>/<feature> and one AI per branch",
            "Prevents overlapping work and preserves clear ownership during collaboration",
            examples=[
                "Create branches like ai/codex/interaction-guidelines",
                "Do not reuse or push to another worker's branch",
            ],
            anti_patterns=[
                "Sharing branches across workers concurrently",
                "Using ambiguous branch names without owner identification",
            ],
            validation_method="Check branch naming and ownership rules in documentation",
            source_documents=["AGENTS.md", "AI_AGENT_HANDBOOK.md"],
        )

        self.define_constraint(
            "COMMUNICATION-005",
            ConstraintArea.COMMUNICATION,
            Severity.IMPORTANT,
            "Architect mediates handoffs/merges; commit and PR descriptions must summarize scope, constraints, tests, and avoid force-push over others",
            "Maintains safe collaboration, reviewability, and stakeholder visibility",
            examples=[
                "PR uses stakeholder template with tests run and constraints honored",
                "On conflicts, stop and escalate instead of force-pushing",
            ],
            anti_patterns=[
                "Merging over another worker without coordination",
                "Force-pushing to resolve conflicts silently",
            ],
            validation_method="Verify collaboration workflow rules and PR standards are documented",
            source_documents=["AGENTS.md", "AI_AGENT_HANDBOOK.md"],
        )

        # Add more constraints for IMPORTANT and RECOMMENDED levels...
        # (This would continue with the full constraint set from the analysis)

    def _get_applicable_constraints(
        self, code_change: dict[str, Any]
    ) -> list[Constraint]:
        """Determine which constraints apply to a specific code change."""
        applicable = []

        # Extract information from code change
        file_paths = code_change.get("file_paths", [])
        operation_type = code_change.get("operation_type", "")
        affected_areas = code_change.get("affected_areas", [])

        # Determine relevant constraint areas
        relevant_areas = set()

        # File path based area detection
        for file_path in file_paths:
            if "gui/" in file_path or "taskpanel" in file_path.lower():
                relevant_areas.add(ConstraintArea.UI)
                relevant_areas.add(ConstraintArea.HYDRATION)
            if "core/" in file_path:
                relevant_areas.add(ConstraintArea.MEASUREMENT)
                relevant_areas.add(ConstraintArea.EXPORT)
            if "test" in file_path.lower():
                relevant_areas.add(ConstraintArea.TESTING)
            if file_path.endswith(".py"):
                relevant_areas.add(ConstraintArea.PYTHON)

        # Operation type based area detection
        if "export" in operation_type.lower():
            relevant_areas.add(ConstraintArea.EXPORT)
        if "ui" in operation_type.lower() or "taskpanel" in operation_type.lower():
            relevant_areas.add(ConstraintArea.UI)
            relevant_areas.add(ConstraintArea.HYDRATION)

        # Add explicitly specified areas
        for area_name in affected_areas:
            try:
                relevant_areas.add(ConstraintArea(area_name.upper()))
            except ValueError:
                pass  # Invalid area name

        # Get constraints for relevant areas
        for constraint in self.constraints.values():
            if constraint.area in relevant_areas:
                applicable.append(constraint)

        return applicable

    def _validate_constraint(
        self, constraint: Constraint, code_change: dict[str, Any]
    ) -> bool:
        """
        Validate a specific constraint against a code change.

        This is a simplified validation - in practice, this would involve
        more sophisticated code analysis.
        """
        # For now, return True (compliant) - real implementation would
        # perform actual code analysis based on constraint.validation_method
        return True

    def _determine_relevant_areas(
        self, task_type: str, file_paths: list[str] = None
    ) -> list[ConstraintArea]:
        """Determine relevant constraint areas based on task type and file paths."""
        relevant_areas = []

        # Task type based area mapping
        task_area_mapping = {
            "hydration": [ConstraintArea.HYDRATION, ConstraintArea.UI],
            "ui": [ConstraintArea.UI, ConstraintArea.HYDRATION],
            "export": [ConstraintArea.EXPORT, ConstraintArea.MEASUREMENT],
            "measurement": [ConstraintArea.MEASUREMENT],
            "testing": [ConstraintArea.TESTING],
            "repository": [ConstraintArea.REPOSITORY],
            "python": [ConstraintArea.PYTHON],
            "communication": [ConstraintArea.COMMUNICATION],
        }

        # Add areas based on task type
        if task_type.lower() in task_area_mapping:
            relevant_areas.extend(task_area_mapping[task_type.lower()])

        # Add areas based on file paths
        if file_paths:
            for file_path in file_paths:
                if "gui/" in file_path or "taskpanel" in file_path.lower():
                    relevant_areas.extend([ConstraintArea.UI, ConstraintArea.HYDRATION])
                if "core/" in file_path:
                    relevant_areas.extend(
                        [ConstraintArea.MEASUREMENT, ConstraintArea.EXPORT]
                    )
                if "test" in file_path.lower():
                    relevant_areas.append(ConstraintArea.TESTING)
                if file_path.endswith(".py"):
                    relevant_areas.append(ConstraintArea.PYTHON)

        # Remove duplicates and return
        return list(set(relevant_areas))


# Global constraint framework instance
constraint_framework = ConstraintFramework()
