# Release Notes

## Unreleased

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
- Documentation and automation: MVP scope, architecture overview, testing guide, and Codex workflow playbooks published to the MkDocs site.

### Notes & known gaps
- Prototype focuses on rectangular panels; curved/grain-aware nesting and richer previews are future work.
- Expect iteration on export formats (DXF/SVG), material-aware optimization, and UI polish in subsequent releases.
