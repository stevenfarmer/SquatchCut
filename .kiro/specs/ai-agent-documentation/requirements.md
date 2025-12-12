# AI Agent Documentation Enhancement Requirements

## Introduction

This specification defines the enhancement of SquatchCut's documentation to provide comprehensive, unambiguous guidelines for AI agents working on the project. The goal is to create documentation that prevents AI agents from inadvertently breaking existing architecture, patterns, or functionality while enabling them to contribute effectively to features and bug fixes.

## Glossary

- **AI Agent**: Any artificial intelligence system (local editor assistants, hosted coding agents, or other automated tools) that performs code implementation, documentation updates, or testing tasks
- **Architect**: The human planner/reviewer who defines tasks, sets guardrails, and writes specifications for AI workers
- **Foundation Architecture**: The core established patterns, behaviors, and architectural decisions that must be preserved
- **Guardrails**: Explicit constraints and boundaries that prevent AI agents from making destructive or counterproductive changes
- **Reasoning Level**: A classification system (LOW, MEDIUM, HIGH, EXTRA-HIGH) that indicates the complexity and risk level of a task
- **Instruction Block**: A structured format for providing clear, unambiguous directions to AI agents
- **Hydration Rules**: The specific initialization and state management patterns that must be followed in SquatchCut
- **Measurement System Architecture**: The internal millimeter storage with imperial fractional display patterns

## Requirements

### Requirement 1

**User Story:** As a project maintainer, I want comprehensive AI agent guidelines that prevent architectural drift, so that multiple AI agents can work on the project without breaking established patterns or introducing inconsistencies.

#### Acceptance Criteria

1. WHEN an AI agent reads the documentation THEN the system SHALL provide explicit architectural constraints that cannot be violated
2. WHEN an AI agent encounters ambiguous requirements THEN the documentation SHALL provide clear decision-making frameworks and escalation paths
3. WHEN an AI agent works on hydration-related code THEN the documentation SHALL specify the exact initialization order and rules that must be followed
4. WHEN an AI agent modifies measurement system code THEN the documentation SHALL enforce the internal millimeter storage with imperial fractional display pattern
5. WHEN an AI agent works on UI components THEN the documentation SHALL specify the exact TaskPanel patterns and widget creation rules

### Requirement 2

**User Story:** As an AI agent, I want clear task specification formats and reasoning level guidelines, so that I can understand the scope, complexity, and constraints of my assigned work without making assumptions.

#### Acceptance Criteria

1. WHEN receiving a task specification THEN the AI agent SHALL be provided with explicit reasoning level declarations (LOW, MEDIUM, HIGH, EXTRA-HIGH)
2. WHEN working on LOW reasoning tasks THEN the AI agent SHALL understand these are trivial fixes in single files with minimal risk
3. WHEN working on HIGH reasoning tasks THEN the AI agent SHALL understand these involve multi-file changes touching settings, hydration, or TaskPanel initialization
4. WHEN task specifications are provided THEN they SHALL include explicit file paths, operation lists, expected behavior, and acceptance criteria
5. WHEN encountering EXTRA-HIGH reasoning tasks THEN the AI agent SHALL understand these require architectural or algorithm-level changes with maximum caution

### Requirement 3

**User Story:** As a project maintainer, I want AI agents to follow strict testing requirements, so that all code changes include appropriate test coverage and maintain system reliability.

#### Acceptance Criteria

1. WHEN an AI agent makes logic-level changes THEN the system SHALL require accompanying tests under the tests/ directory
2. WHEN an AI agent modifies core functionality THEN the documentation SHALL specify the exact testing patterns and frameworks to use
3. WHEN an AI agent works on measurement system code THEN the system SHALL require tests for mm/inch conversions and fractional parsing
4. WHEN an AI agent modifies hydration logic THEN the system SHALL require tests for default initialization and preset behavior
5. WHEN an AI agent updates UI components THEN the system SHALL specify the GUI testing patterns and qt_compat usage requirements

### Requirement 4

**User Story:** As a project maintainer, I want AI agents to understand and preserve the export architecture, so that all user-facing exports maintain consistency and use the canonical data models.

#### Acceptance Criteria

1. WHEN an AI agent works on export functionality THEN the system SHALL enforce that all exports go through freecad/SquatchCut/core/exporter.py
2. WHEN an AI agent modifies export code THEN the documentation SHALL specify that ExportJob/ExportSheet/ExportPartPlacement are the only sources of truth
3. WHEN an AI agent implements new export formats THEN the system SHALL require using ExportJob values in millimeters with exporter helpers for display strings
4. WHEN an AI agent encounters export requirements THEN the documentation SHALL explicitly state that DXF export is deferred and should not be implemented
5. WHEN an AI agent works on CSV or SVG exports THEN the system SHALL enforce deterministic behavior driven solely by ExportJob data

### Requirement 5

**User Story:** As an AI agent, I want clear interaction protocols and communication guidelines, so that I can effectively collaborate with human stakeholders and other AI agents without causing conflicts or misunderstandings.

#### Acceptance Criteria

1. WHEN interacting with non-technical stakeholders THEN the AI agent SHALL act as Lead Developer and Product Manager for day-to-day interactions
2. WHEN requirements are high-level or vague THEN the AI agent SHALL follow the Discovery Process with clarifying questions before implementation
3. WHEN working on overlapping code regions THEN the AI agent SHALL understand branch isolation rules and coordination requirements
4. WHEN completing tasks THEN the AI agent SHALL provide stakeholder-friendly PR descriptions with plain English summaries
5. WHEN encountering errors or ambiguity THEN the AI agent SHALL follow specified escalation and self-correction protocols

### Requirement 6

**User Story:** As a project maintainer, I want AI agents to understand Python version constraints and compatibility requirements, so that all code remains compatible with older Python versions used in FreeCAD environments.

#### Acceptance Criteria

1. WHEN an AI agent writes Python code THEN the system SHALL enforce compatibility with Python versions older than 3.10
2. WHEN an AI agent uses type annotations THEN the documentation SHALL prohibit PEP 604 type unions (type | None) and require Optional[type]
3. WHEN an AI agent imports modules THEN the system SHALL prohibit relative imports, especially in FreeCAD integration code
4. WHEN an AI agent works with FreeCAD APIs THEN the documentation SHALL specify the exact import patterns and compatibility requirements
5. WHEN an AI agent encounters modern Python features THEN the system SHALL provide alternative patterns compatible with older Python versions

### Requirement 7

**User Story:** As a project maintainer, I want AI agents to understand the repository layout and file organization rules, so that code remains properly organized and architectural boundaries are respected.

#### Acceptance Criteria

1. WHEN an AI agent creates or modifies files THEN the system SHALL enforce the established directory structure with core/, gui/, resources/, tests/, and docs/ separation
2. WHEN an AI agent works on core logic THEN the documentation SHALL specify that changes belong in freecad/SquatchCut/core/ with specific module responsibilities
3. WHEN an AI agent works on UI components THEN the system SHALL enforce that changes belong in freecad/SquatchCut/gui/ with TaskPanel and view organization
4. WHEN an AI agent adds tests THEN the documentation SHALL specify the tests/ directory structure and naming conventions
5. WHEN an AI agent updates documentation THEN the system SHALL specify the docs/ organization and required documentation standards

### Requirement 8

**User Story:** As an AI agent, I want comprehensive examples and anti-patterns documentation, so that I can understand not just what to do, but what specifically to avoid based on past issues and architectural decisions.

#### Acceptance Criteria

1. WHEN learning about hydration THEN the AI agent SHALL be provided with specific examples of correct and incorrect initialization patterns
2. WHEN working with measurement systems THEN the documentation SHALL include examples of proper mm/fractional inch handling and common mistakes to avoid
3. WHEN modifying UI components THEN the AI agent SHALL be shown examples of correct TaskPanel patterns and anti-patterns that cause issues
4. WHEN working with presets and defaults THEN the documentation SHALL provide clear examples of the separation between these concepts
5. WHEN implementing export functionality THEN the AI agent SHALL be given examples of correct ExportJob usage and patterns to avoid

### Requirement 9

**User Story:** As a project maintainer, I want AI agents to understand performance and quality constraints, so that all contributions maintain system performance and code quality standards.

#### Acceptance Criteria

1. WHEN an AI agent implements algorithms THEN the documentation SHALL specify performance expectations and optimization requirements
2. WHEN an AI agent writes code THEN the system SHALL enforce self-correction protocols with maximum retry limits before escalation
3. WHEN an AI agent makes destructive changes THEN the documentation SHALL require explicit consequence explanation and user confirmation
4. WHEN an AI agent encounters errors THEN the system SHALL specify the exact error handling and reporting protocols
5. WHEN an AI agent works on critical paths THEN the documentation SHALL identify performance-sensitive areas and optimization requirements

### Requirement 10

**User Story:** As a project maintainer, I want AI agents to understand version control and collaboration workflows, so that multiple agents can work simultaneously without conflicts while maintaining code quality.

#### Acceptance Criteria

1. WHEN multiple AI agents work on the project THEN the system SHALL enforce one AI per branch with clear naming conventions
2. WHEN AI agents need to collaborate THEN the documentation SHALL specify that the Architect mediates through merge and reassign rather than concurrent edits
3. WHEN AI agents complete work THEN the system SHALL require proper commit messages and PR descriptions following stakeholder communication standards
4. WHEN AI agents encounter merge conflicts THEN the documentation SHALL provide clear resolution protocols and escalation paths
5. WHEN AI agents work on sequential tasks THEN the system SHALL specify the coordination and handoff procedures between agents

### Requirement 11

**User Story:** As a project maintainer, I want AI agents to maintain accurate and current backlog documentation, so that the project backlog reflects only active open issues and needed enhancements without completed or obsolete items.

#### Acceptance Criteria

1. WHEN an AI agent updates project documentation THEN the system SHALL require review and cleanup of backlog files to remove completed features
2. WHEN an AI agent encounters completed backlog items THEN the documentation SHALL specify that these items must be marked as completed or removed entirely
3. WHEN an AI agent reviews the current backlog THEN the system SHALL ensure it consists only of active open known issues and feature enhancements that are still needed
4. WHEN an AI agent works on backlog management THEN the documentation SHALL specify the criteria for determining if an item is complete, obsolete, or still active
5. WHEN an AI agent updates backlog status THEN the system SHALL require verification that completed items have corresponding implementation evidence in the codebase
