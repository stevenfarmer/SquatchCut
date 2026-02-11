# SquatchCut Test Fixtures

This directory holds fixture data for SquatchCut testing.

- CSV fixtures in `csv/` feed validation, preprocessing, and nesting scenarios.
- `expected_summary_small.json` provides a reference summary for the small panel set.
- Helper scripts in `helpers/` can generate FreeCAD documents for geometry-based tests.

## Generating FreeCAD test documents
1. Open FreeCAD.
2. Open the Python console.
3. Run `freecad/testing/helpers/generate_test_documents.py`.
4. This creates basic rectangle documents used by SquatchCut for E2E-style checks.

## Usage
- CSV validation tests
- Nesting tests (single and multi-sheet)
- Future E2E tests

## End-to-End Smoke Tests
- CSV E2E (run inside FreeCAD Python console or FreeCAD-enabled Python):
  ```python
  from SquatchCut.testing.e2e_mvp_csv_flow import main
  main()
  ```
- Geometry E2E:
  ```python
  from SquatchCut.testing.e2e_mvp_geometry_flow import main
  main()
  ```
