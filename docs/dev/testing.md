# Testing

## Fixtures
- FreeCAD fixtures: `freecad/testing/`
- CSV fixtures: `freecad/testing/csv/`, `ts-tools/test-data/`

## FreeCAD E2E
- CSV flow:
  ```python
  from SquatchCut.testing.e2e_mvp_csv_flow import main
  main()
  ```
- Geometry flow:
  ```python
  from SquatchCut.testing.e2e_mvp_geometry_flow import main
  main()
  ```

## TS Tools E2E
```bash
cd ts-tools
npm run build
npm run e2e
```
