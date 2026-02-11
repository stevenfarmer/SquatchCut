# SquatchCut TS Tools

TypeScript utilities for the SquatchCut FreeCAD plugin:

- CSV validation for panel data
- Data normalization helpers
- Preprocessing pipeline to prepare panels for the FreeCAD workbench

## Codex update guidance
- Read @codex headers in `src/` files to understand responsibilities.
- Update modules incrementally; do not overwrite files.
- Keep logic pure and framework-independent.

## Build and lint workflow
- Install deps: `npm install`
- Build: `npm run build`
- Watch build: `npm run dev`
- Lint: `npm run lint`
- Lint (fix): `npm run lint:fix`

## Usage
- Validate & preprocess a CSV after build:
  - `npm run build`
  - `node dist/cli.js path/to/panels.csv`
- As a global-style invocation:
  - `npx squatchcut-csv path/to/panels.csv`

What it does:
- Validates required fields id/width/height.
- Normalizes panel data (trims IDs, filters invalid rows).
- Reports all row errors without aborting on the first one.
- Prepares cleaned panels for use in the SquatchCut FreeCAD plugin.

## E2E CLI test
- After building: `npm run build`
- Then: `npm run e2e`
