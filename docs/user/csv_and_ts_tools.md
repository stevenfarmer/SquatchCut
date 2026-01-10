# CSV & TS Tools

## CSV Panel Format
- Required columns: `id`, `width`, `height`
- Optional: `grain_direction` (or `grainDirection`)
- Units: metric or imperial (the importer/ts-tools normalize to millimeters internally)

## Validation with ts-tools
- The `ts-tools` package validates and normalizes panel CSVs.
- Errors are collected without aborting on first failure.

### CLI Usage
```bash
cd ts-tools
npm run build
npx squatchcut-csv path/to/file.csv
```

## Workflow Integration
- Validate CSVs before importing into FreeCAD.
- Use clean panels to improve nesting outcomes.
