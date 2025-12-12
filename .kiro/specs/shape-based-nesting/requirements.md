# Shape-Based Nesting Requirements

## Introduction

This specification defines the enhancement of SquatchCut to support comprehensive shape-based nesting workflows, allowing users to create cabinet parts and other complex shapes in FreeCAD and efficiently nest them on sheet goods with support for non-rectangular geometries.

## Glossary

- **Shape-Based Nesting**: The process of arranging complex, non-rectangular shapes on sheet materials
- **FreeCAD Object**: Any geometric object created in FreeCAD with a valid Shape property
- **Bounding Box Nesting**: Current rectangular approximation method using object dimensions
- **True Shape Nesting**: Advanced nesting that considers actual object geometry and contours
- **Cabinet Workflow**: The specific use case of designing furniture parts in FreeCAD and nesting them for cutting
- **Shape Extractor**: SquatchCut component that converts FreeCAD objects into nestable panels
- **Nesting Engine**: The core algorithm that arranges shapes on sheets
- **Selection Workflow**: User process of choosing specific FreeCAD objects for nesting

## Requirements

### Requirement 1

**User Story:** As a cabinet maker, I want to design my cabinet parts in FreeCAD and have SquatchCut automatically detect and nest them on plywood sheets, so that I can optimize material usage for complex furniture projects.

#### Acceptance Criteria

1. WHEN a user creates cabinet parts in FreeCAD THEN SquatchCut SHALL detect all objects with valid Shape properties in the active document
2. WHEN SquatchCut scans a document THEN the system SHALL extract dimensional and geometric data from each detected shape
3. WHEN multiple cabinet parts are detected THEN SquatchCut SHALL present them in a selection interface for user review
4. WHEN a user selects specific parts for nesting THEN SquatchCut SHALL process only the selected objects
5. WHEN cabinet parts are processed THEN SquatchCut SHALL preserve part identification and labeling from FreeCAD

### Requirement 2

**User Story:** As a woodworker, I want SquatchCut to support non-rectangular nesting so that I can efficiently nest curved, angled, and complex-shaped parts without wasting material on bounding box approximations.

#### Acceptance Criteria

1. WHEN SquatchCut processes a non-rectangular shape THEN the system SHALL extract the actual geometric contour rather than just the bounding box
2. WHEN performing non-rectangular nesting THEN the system SHALL detect and prevent overlaps between actual shape geometries
3. WHEN nesting complex shapes THEN the system SHALL support rotation of non-rectangular parts while maintaining geometric accuracy
4. WHEN calculating material utilization THEN the system SHALL account for actual shape areas rather than bounding box areas
5. WHEN exporting layouts THEN the system SHALL include accurate shape outlines for cutting guidance

### Requirement 3

**User Story:** As a FreeCAD user, I want an intuitive workflow to select which of my designed parts should be nested, so that I can control exactly what gets included in my cutting layout.

#### Acceptance Criteria

1. WHEN SquatchCut opens the shape selection interface THEN the system SHALL display a list of all detected FreeCAD objects with their names and dimensions
2. WHEN a user views the shape selection list THEN the system SHALL show preview thumbnails or descriptions for each detected shape
3. WHEN a user selects shapes for nesting THEN the system SHALL provide checkboxes or similar selection controls for each item
4. WHEN a user confirms their selection THEN SquatchCut SHALL proceed with nesting only the chosen shapes
5. WHEN no shapes are selected THEN the system SHALL prevent nesting and display an appropriate message

### Requirement 4

**User Story:** As a quality-focused developer, I want comprehensive test coverage for shape-based nesting across multiple scenarios, so that users can rely on accurate and consistent nesting results.

#### Acceptance Criteria

1. WHEN testing shape extraction THEN the system SHALL validate extraction from simple boxes, complex curves, and mixed geometry documents
2. WHEN testing non-rectangular nesting THEN the system SHALL verify correct placement without overlaps for various shape combinations
3. WHEN testing the selection workflow THEN the system SHALL validate proper UI behavior for selecting, deselecting, and confirming shape choices
4. WHEN testing cabinet workflows THEN the system SHALL validate end-to-end scenarios from FreeCAD design to final cutting layout
5. WHEN testing edge cases THEN the system SHALL handle invalid shapes, empty documents, and malformed geometry gracefully

### Requirement 5

**User Story:** As a SquatchCut user, I want clear documentation on how to use shape-based nesting features, so that I can effectively integrate FreeCAD design workflows with my cutting optimization process.

#### Acceptance Criteria

1. WHEN users access SquatchCut documentation THEN the system SHALL provide step-by-step guides for the cabinet maker workflow
2. WHEN users need technical reference THEN the documentation SHALL explain the differences between rectangular and non-rectangular nesting modes
3. WHEN users encounter issues THEN the documentation SHALL include troubleshooting guides for common shape extraction problems
4. WHEN users want examples THEN the documentation SHALL provide sample FreeCAD files and expected nesting results
5. WHEN users need API reference THEN the documentation SHALL document all shape extraction and nesting configuration options

### Requirement 6

**User Story:** As a SquatchCut maintainer, I want robust GUI tests that validate the shape selection and nesting workflows, so that UI changes don't break critical user functionality.

#### Acceptance Criteria

1. WHEN GUI tests run THEN the system SHALL validate the shape selection dialog opens and displays detected shapes correctly
2. WHEN testing selection interactions THEN the system SHALL verify checkbox behavior, selection state management, and confirmation actions
3. WHEN testing nesting integration THEN the system SHALL validate that selected shapes properly flow into the nesting engine
4. WHEN testing error scenarios THEN the system SHALL verify appropriate error messages for invalid selections or failed operations
5. WHEN testing across measurement systems THEN the system SHALL validate shape extraction works correctly in both metric and imperial modes

### Requirement 7

**User Story:** As a performance-conscious user, I want shape-based nesting to handle complex documents efficiently, so that I can work with realistic cabinet projects without excessive processing delays.

#### Acceptance Criteria

1. WHEN processing documents with many shapes THEN SquatchCut SHALL complete shape extraction within reasonable time limits
2. WHEN nesting complex geometries THEN the system SHALL provide progress feedback for long-running operations
3. WHEN handling large shapes THEN the system SHALL manage memory usage efficiently to prevent crashes
4. WHEN users work with detailed geometry THEN SquatchCut SHALL offer simplified nesting modes for faster processing
5. WHEN processing fails due to complexity THEN the system SHALL gracefully fall back to bounding box nesting with user notification

### Requirement 8

**User Story:** As a precision-focused woodworker, I want accurate kerf and margin handling for non-rectangular shapes, so that my cut parts will fit together properly after machining.

#### Acceptance Criteria

1. WHEN applying kerf compensation to non-rectangular shapes THEN SquatchCut SHALL adjust the actual shape geometry rather than just the bounding box
2. WHEN setting margins between complex shapes THEN the system SHALL maintain specified distances between actual shape contours
3. WHEN rotating non-rectangular parts THEN the system SHALL preserve kerf and margin settings in the new orientation
4. WHEN exporting cutting layouts THEN the system SHALL include kerf-compensated geometry for accurate machining
5. WHEN validating fit THEN the system SHALL verify that kerf-adjusted shapes still fit within sheet boundaries
