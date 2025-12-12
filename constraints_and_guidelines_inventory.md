# SquatchCut Constraints and Guidelines Inventory

## Overview

This document provides a comprehensive inventory of all existing constraints and guidelines found across SquatchCut's documentation, organized by category and severity level.

## Constraint Categories and Severity Levels

### Severity Levels
- **CRITICAL:** Cannot be violated under any circumstances
- **IMPORTANT:** Should not be violated without explicit approval
- **RECOMMENDED:** Best practices that improve maintainability

### Categories
- **HYDRATION:** Initialization and state management patterns
- **MEASUREMENT:** Unit conversion and display patterns
- **EXPORT:** Data export architecture and patterns
- **UI:** User interface behavior and patterns
- **TESTING:** Test requirements and patterns
- **REPOSITORY:** File organization and structure
- **PYTHON:** Language compatibility requirements
- **COMMUNICATION:** AI agent interaction protocols

## CRITICAL Constraints (Non-Negotiable)

### HYDRATION-001: Initialization Order
**Rule:** hydrate_from_params() MUST be called before creating UI widgets
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Ensures consistent state initialization and prevents UI/data mismatches
**Validation:** Check TaskPanel initialization order in all UI code

### HYDRATION-002: Default Persistence
**Rule:** Defaults MUST only change via Settings panel save operations
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Prevents accidental default modifications and maintains user expectations
**Validation:** Verify no default modifications outside Settings save flow

### HYDRATION-003: Preset Auto-Selection Prohibition
**Rule:** Presets MUST NEVER be auto-selected on panel load
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Maintains clear separation between defaults and presets
**Validation:** Check that preset selection always starts as "None/Custom"

### MEASUREMENT-001: Internal Unit Standard
**Rule:** Internal storage MUST always use millimeters
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Ensures consistent calculations and prevents conversion errors
**Validation:** Verify all internal calculations use mm units

### MEASUREMENT-002: Imperial Display Format
**Rule:** Imperial UI MUST use fractional inches only (no decimals)
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Matches woodworking industry standards and user expectations
**Validation:** Check all imperial display formatting uses fractions

### EXPORT-001: Canonical Export Architecture
**Rule:** All exports MUST go through freecad/SquatchCut/core/exporter.py
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Ensures consistent export behavior and data integrity
**Validation:** Verify no direct export implementations outside exporter.py

### EXPORT-002: ExportJob Source of Truth
**Rule:** ExportJob/ExportSheet/ExportPartPlacement MUST be the only sources of truth for export geometry
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Prevents inconsistencies between FreeCAD geometry and export data
**Validation:** Check that exports never derive from FreeCAD document objects when ExportJob exists

### PYTHON-001: Version Compatibility
**Rule:** Code MUST be compatible with Python versions older than 3.10
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** FreeCAD compatibility requirements
**Validation:** Check for PEP 604 unions and other modern Python features

### PYTHON-002: Import Pattern Restriction
**Rule:** No relative imports, especially in FreeCAD integration code
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** FreeCAD module loading compatibility
**Validation:** Scan for relative import statements

### UI-001: Settings Panel Availability
**Rule:** Settings panel MUST always open successfully
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Critical for user configuration and system functionality
**Validation:** Test Settings panel opening under all conditions

## IMPORTANT Constraints (Require Approval to Violate)

### REPOSITORY-001: Directory Structure
**Rule:** Maintain established directory structure (core/, gui/, resources/, tests/, docs/)
**Source:** AGENTS.md, architecture.md
**Rationale:** Maintains architectural boundaries and code organization
**Validation:** Check file placement against established structure

### REPOSITORY-002: Module Responsibilities
**Rule:** Respect module responsibility boundaries defined in architecture.md
**Source:** architecture.md, Project_Guide_v3.3.md
**Rationale:** Prevents architectural drift and maintains separation of concerns
**Validation:** Verify code placement matches module responsibilities

### UI-002: TaskPanel Initialization Pattern
**Rule:** Follow specific TaskPanel initialization order (session_state → hydrate → widgets → populate → format → signals → render)
**Source:** Project_Guide_v3.3.md
**Rationale:** Ensures consistent UI behavior and prevents initialization errors
**Validation:** Check TaskPanel initialization sequences

### UI-003: Group Management Pattern
**Rule:** Clear groups before redraw, maintain consistent naming (SquatchCut_Sheet, SquatchCut_SourceParts, SquatchCut_NestedParts)
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Prevents orphaned objects and maintains document cleanliness
**Validation:** Check group clearing and naming patterns

### MEASUREMENT-003: UI Reformatting Requirements
**Rule:** Switching measurement systems requires full reformatting of all numeric UI fields
**Source:** Project_Guide_v3.3.md
**Rationale:** Ensures UI consistency and prevents display errors
**Validation:** Test measurement system switching behavior

### TESTING-001: Logic Change Testing Requirement
**Rule:** Any logic-level change must be accompanied by tests under tests/
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Maintains code quality and prevents regressions
**Validation:** Check for corresponding tests with logic changes

### COMMUNICATION-001: Stakeholder Interaction Protocol
**Rule:** AI agents must act as Lead Developer & Product Manager for day-to-day interactions
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Ensures appropriate communication level with non-technical stakeholders
**Validation:** Review interaction patterns and communication style

### COMMUNICATION-002: Branch Isolation
**Rule:** One AI per branch, no overlapping edits on same core files in parallel
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Prevents merge conflicts and coordination issues
**Validation:** Check branch usage patterns and file edit conflicts

## RECOMMENDED Guidelines (Best Practices)

### TESTING-002: Core Focus Areas
**Rule:** Prioritize testing for mm/inch conversions, CSV parsing, hydration, preset behavior
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** These areas are most prone to errors and critical for functionality
**Validation:** Review test coverage in these areas

### TESTING-003: GUI Testing Patterns
**Rule:** Use qt_compat shim for GUI tests, manually invoke slots when needed
**Source:** AGENTS.md, TESTING.md
**Rationale:** Enables headless testing and consistent test behavior
**Validation:** Check GUI test implementation patterns

### PYTHON-003: Type Annotation Patterns
**Rule:** Use Optional[type] instead of type | None for compatibility
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Maintains compatibility with older Python versions
**Validation:** Check type annotation patterns

### UI-004: Overflow Prevention
**Rule:** UI must not overflow or fail to load, especially on narrow docks
**Source:** Project_Guide_v3.3.md, backlog.md
**Rationale:** Ensures usability across different screen configurations
**Validation:** Test UI at various dock widths

### EXPORT-003: DXF Export Deferral
**Rule:** DXF export is explicitly deferred and should not be implemented
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Scope management and delivery focus
**Validation:** Check for DXF implementation attempts

### COMMUNICATION-003: Discovery Process
**Rule:** Use clarifying questions for high-level or vague requirements before implementation
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Prevents incorrect assumptions and ensures proper requirements understanding
**Validation:** Review requirement clarification patterns

### COMMUNICATION-004: PR Description Format
**Rule:** Use stakeholder-friendly PR descriptions with plain English summaries
**Source:** AGENTS.md, Project_Guide_v3.3.md
**Rationale:** Ensures clear communication of changes to non-technical stakeholders
**Validation:** Review PR description formats

## Constraint Enforcement Mechanisms

### Current Enforcement
1. **Documentation Review:** Manual checking against documented constraints
2. **Code Review:** Human review of constraint compliance
3. **Testing:** Some constraints validated through test suites
4. **CI/CD:** Limited automated constraint checking

### Missing Enforcement
1. **Automated Constraint Validation:** No systematic automated checking
2. **Constraint Violation Detection:** No automated detection of violations
3. **Escalation Procedures:** No systematic escalation for constraint conflicts
4. **Compliance Reporting:** No systematic compliance tracking

## Pain Points and Ambiguities

### 1. Severity Level Ambiguity
**Problem:** No clear distinction between CRITICAL and IMPORTANT constraints
**Impact:** Inconsistent enforcement decisions
**Example:** UI overflow prevention vs Settings panel availability

### 2. Constraint Conflict Resolution
**Problem:** No procedures for handling conflicting constraints
**Impact:** Blocked progress when constraints conflict
**Example:** Performance optimization vs testing requirements

### 3. Validation Procedures
**Problem:** Many constraints lack specific validation procedures
**Impact:** Inconsistent compliance checking
**Example:** "Respect module responsibilities" without specific validation steps

### 4. Escalation Triggers
**Problem:** Unclear when to escalate constraint-related issues
**Impact:** Delayed resolution of constraint conflicts
**Example:** When architectural changes require constraint modifications

### 5. Context-Dependent Application
**Problem:** Some constraints may not apply in all contexts
**Impact:** Over-rigid application or inappropriate exceptions
**Example:** Testing requirements for prototype vs production code

## Recommendations for Improvement

### 1. Systematic Constraint Classification
- Implement formal severity level definitions
- Create constraint categories with clear boundaries
- Develop constraint conflict resolution procedures

### 2. Automated Validation Framework
- Implement automated constraint checking tools
- Create constraint violation detection systems
- Develop compliance reporting mechanisms

### 3. Clear Escalation Procedures
- Define escalation triggers and procedures
- Establish decision-making authority hierarchy
- Create constraint modification approval processes

### 4. Comprehensive Examples
- Provide concrete examples for each constraint
- Document anti-patterns and common violations
- Create constraint application guidelines

### 5. Regular Constraint Review
- Establish periodic constraint review processes
- Update constraints based on project evolution
- Maintain constraint documentation currency

## Conclusion

This inventory reveals a comprehensive but scattered set of constraints and guidelines. The main issues are:

1. **Inconsistent severity classification** leading to enforcement ambiguity
2. **Missing validation procedures** for many constraints
3. **Unclear escalation procedures** for constraint conflicts
4. **Scattered documentation** making systematic compliance difficult
5. **Limited automated enforcement** requiring manual checking

Addressing these issues through systematic constraint framework implementation will significantly improve AI agent compliance and prevent architectural drift.
