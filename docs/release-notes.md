# Release Notes

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
