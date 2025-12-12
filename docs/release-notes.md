# Release Notes

## Unreleased

### Advanced Features Implementation

#### Major New Features
- **Advanced Nesting Algorithms**: Genetic algorithm optimization system
  - Multi-objective fitness function for optimal part placement
  - Configurable population size, generations, and mutation rates
  - Grain direction support for wood nesting applications
  - Automatic termination when target utilization is reached
  - Performance monitoring and progress tracking

- **Enhanced Export Capabilities**: Professional export options
  - SVG export with cut lines and waste area visualization
  - DXF export with organized layers for CNC compatibility
  - Enhanced CSV exports with measurement system formatting
  - Multi-sheet export support with proper scaling

- **Smart Cut Optimization**: Automated cutting sequence planning
  - Optimal cut order planning (rip cuts first, then crosscuts)
  - Material handling optimization to minimize setup time
  - Cut length optimization and time estimation
  - Integration with export systems for workshop planning

- **Quality Assurance System**: Comprehensive layout validation
  - Overlap detection and bounds compliance checking
  - Spacing requirements validation and rotation consistency
  - Dimension consistency verification against original parts
  - Quality scoring system (0-100) with detailed reports
  - Automatic quality checks after nesting operations

- **Performance Enhancements**: Optimization for large datasets
  - Intelligent caching system (memory and disk-based)
  - Multi-threading support for parallel processing
  - Memory optimization for large part lists
  - Configurable performance settings and monitoring

### UI/UX Enhancements & Performance Improvements

#### New Features
- **Keyboard Shortcuts**: Added comprehensive keyboard shortcuts for common operations (Ctrl+I for import, Ctrl+R/F5 for nesting, Ctrl+E for export, etc.)
- **Progress Indicators**: Long-running operations now show progress dialogs with visual feedback and estimated completion times
- **Enhanced Error Handling**: Standardized error messages with clear descriptions, technical details, and actionable recovery instructions
- **Performance Monitoring**: Automatic detection and logging of slow operations with configurable thresholds
- **Large Dataset Support**: Optimized handling of 1000+ parts with memory management and resource warnings

#### Enhanced Nesting View
- **Color Schemes**: Multiple color palettes including high-contrast accessibility options
- **Display Modes**: Choose between transparent, wireframe, or solid part visualization
- **Sheet Layouts**: Options for side-by-side or stacked sheet arrangements
- **Part Labels**: Optional display of part IDs and names on nested pieces
- **Quick Toggles**: Easy controls for common view adjustments

#### Developer Improvements
- **Input Validation Framework**: Comprehensive validation utilities for user inputs with proper error handling
- **Performance Utils**: Decorators and utilities for monitoring performance and handling large datasets
- **Batch Processing**: Memory-efficient processing utilities for large operations
- **Progress Tracking**: Reusable progress tracking components with ETA calculations

#### Bug Fixes
- Fixed quantity validation edge case where 0 was treated as default value
- Corrected imperial unit conversion in validation functions
- Improved filename sanitization for export operations
- Enhanced error propagation in panel validation

#### Testing
- Added 68 new tests covering UI interactions, performance utilities, and input validation
- Comprehensive test coverage for error conditions and edge cases
- Accessibility testing framework for keyboard navigation and screen reader support

## Previous Release

### Highlights
- Per-part 0°/90° rotation support driven by optional `allow_rotate` CSV column and `SquatchCutCanRotate` property; defaults to no rotation when missing.
- Separate kerf (between adjacent parts) and gap/halo (around parts and sheet edges) controls passed into nesting.
- New Export Nesting CSV command with a save dialog; exports sheet index, part id, true dimensions, x/y, and angle without inflating sizes.
- Hardened CSV import with required-column validation, per-row skipping with warnings, and user-facing error dialogs.
- Units preference (mm/in) for sheet sizing and CSV import, plus CSV units selector in the task panel.
- Fixed sheet size defaults so factory values align with the active units, user defaults persist across reloads, and the preset dropdown only highlights exact matches while remaining blank otherwise.
- Centralized view switching so source vs nested views now rely on a controller that hides irrelevant geometry, fits the camera, and cleans out stale layouts before each nesting run.
- Export Cutlist command for CSV rip/crosscut lists, with cutline de-duplication and panel-crossing filters to reduce noise.

### Notes
- `allow_rotate` is optional; omitting the column keeps rotation disabled for all parts.
- Kerf applies only between parts; gap pushes parts away from sheet edges.

## v0.1.0 — First prototype release

### Highlights
- FreeCAD workbench scaffolded with core commands: Add Shapes, Import CSV, Set Sheet Size, Run Nesting, Export Report, and Preferences.
- Nesting backend handles panel extraction, CSV loading, multi-sheet rectangular nesting (Skyline/Guillotine hybrid), geometry generation, and report exports.
- TypeScript CSV validation/preprocessing CLI (`npx squatchcut-csv`) for sanitizing panel lists before import.
- End-to-end coverage: FreeCAD CSV and geometry flows, plus Node-based CLI smoke tests with shared fixtures.
- Documentation and automation: MVP scope, architecture overview, testing guide, and AI worker workflow playbooks published to the MkDocs site.

### Notes & known gaps
- Prototype focuses on rectangular panels; curved/grain-aware nesting and richer previews are future work.
- Expect iteration on export formats (DXF/SVG), material-aware optimization, and UI polish in subsequent releases.
