# 🦶 SquatchCut  
### A Cryptid-Powered Nesting Workbench for FreeCAD

SquatchCut is a custom FreeCAD workbench designed to handle woodworking sheet optimization:  
extract shapes → auto-generate panel data → run nesting → produce cut geometry → export reports.

This project includes:

- A full FreeCAD Workbench (`SquatchCut`)
- A Python backend for nesting and geometry generation
- A GUI layer with dialogs and commands
- A TypeScript toolchain for CSV validation/preprocessing
- E2E smoke tests for both the FreeCAD and TS sides
- Automated Codex workflows for AI-driven development

SquatchCut is designed for real-world workshop use, but completely open and extendable.

---

## 🏗️ Features (MVP)

### **FreeCAD Workbench**
- Extract rectangles/panels from active FreeCAD document  
- CSV import for panel lists (optional `allow_rotate` column; defaults to no rotation)  
- User-configurable sheet size + separate kerf (between parts) and gap/halo (around parts)  
- Multi-sheet rectangular nesting (Skyline / Guillotine hybrid) with per-part 0°/90° rotation  
- Generate 2D panel layout geometry per sheet  
- Export PDF + CSV nesting reports, plus an on-demand “Export Nesting CSV” dialog  
- Preferences pane integration  

### **TypeScript Tools**
- CSV validator + preprocessor (`ts-tools/`)  
- CLI for validating panel lists:  
  ```
  npx squatchcut-csv path/to/panels.csv
  ```
- Helps sanitize data before importing into FreeCAD

### **Testing**
- Python E2E tests (CSV → Nesting → Report)  
- Python E2E tests for FreeCAD geometry extraction  
- Node CLI E2E tests for TS tools  
- Fixture CSVs and FreeCAD geometry generators  

---

## 📁 Repository Structure

```
freecad/
  SquatchCut/
    core/            # backend logic
    gui/             # commands + dialogs
    resources/       # icons, branding
    testing/         # E2E + fixtures

ts-tools/
  src/               # validator, preprocessors, cli
  dist/
  test-data/
  tests/

docs/
  architecture.md
  mvp.md
  codex_workflows.md
```

---

## ⚙️ Installing & Enabling the Workbench (FreeCAD)

1. Clone the repo into FreeCAD’s Mod directory:

   **Linux/macOS**
   ```
   ~/.local/share/FreeCAD/Mod/
   ```
   **Windows**
   ```
   %APPDATA%\\FreeCAD\\Mod\\
   ```

2. Restart FreeCAD.

3. Choose **SquatchCut** from the Workbench dropdown.

4. You should see a new toolbar:  
   - Add Shapes  
   - Import CSV  
   - Run Nesting  
   - Sheet Size  
   - Export Report  
   - Preferences  

---

## 🚀 Using SquatchCut (MVP Flow)

### **1. Add panels**
Either:
- Select rectangles in the document → click **Add Shapes**  
or  
- Click **Import CSV** and load a panel list

### **2. Set sheet size**
Use **Sheet Size**  
(Hard defaults: 2440 × 1220 mm)

### **3. Run Nesting**
Click **Run Nesting**  
You will receive:
- A group for each sheet  
- Rectangles representing panel placements  
- A summary stored in memory for reporting  
- A “SourcePanels” group containing the originals (hidden by default)  
- Optional rotation of parts if `allow_rotate` is set for that row in the CSV  

### **4. Export Report**
Choose a directory → PDF + CSV written there.

### **5. Export Nesting CSV**
Use **Export Nesting CSV** to save the most recent layout as a CSV to a path you choose.  
The export includes sheet index, part id, true width/height, x/y, and chosen angle (0 or 90).  
Kerf and gap are layout parameters only and are not included in the dimensions.

---

## 🧪 Testing

### **FreeCAD E2E Tests**
Inside FreeCAD Python console:

```
from SquatchCut.testing.e2e_mvp_csv_flow import main
main()
```

Geometry flow test:

```
from SquatchCut.testing.e2e_mvp_geometry_flow import main
main()
```

### **TS Tools E2E Tests**
Inside `ts-tools/`:

```
npm run build
npm run e2e
```

---

## 🔧 Developer Workflow (Codex Automation)

SquatchCut is built with **embedded `@codex` headers** that turn the project into a  
*context-aware, AI-assisted development environment.*

### **Global Workflow Commands**
You can run these directly in VS Code:

- `@codex implement next core logic`  
- `@codex update feature <X>`  
- `@codex integrate GUI`  
- `@codex sync architecture`  
- `@codex refactor safely`  
- `@codex implementation status`

These commands:
- Respect per-file architecture
- Never overwrite full files
- Update the correct modules
- Maintain strict separation of concerns

See: `docs/codex_workflows.md`

---

## 🛠️ Building the TypeScript Tools

```
cd ts-tools
npm install
npm run build
```

Run validator:

```
npx squatchcut-csv path/to/panels.csv
```

## Running Tests

Install dev dependencies:

```
pip install -r requirements-dev.txt
```

Run tests:

```
pytest
```

With coverage:

```
pytest --cov=SquatchCut.core.nesting --cov=SquatchCut.core.session_state --cov-report=term-missing
```

## Testing

For detailed instructions on how to run core tests, FreeCAD integration tests,
and manual QA checks, see:

```
docs/TESTING.md
```

### Pre-commit Hooks

To automatically run syntax checks and linting before each commit:

1. Install dev dependencies (once):

   ```
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
   ```

2. Install pre-commit hooks (once):

   ```
   pre-commit install
   ```

After this, every `git commit` will automatically:
- Run `check-ast` to catch Python syntax/indent errors.
- Run `ruff` on the SquatchCut source and tests.

You can also run all checks manually with:

```
npm run check
```

## Integration Tests (FreeCAD-based)

In addition to the core Python tests, SquatchCut provides integration tests
that run inside FreeCAD and exercise the actual workbench commands.

1. Ensure your SquatchCut workbench is installed in a location FreeCAD can see
   (for example `~/.FreeCAD/Mod/SquatchCut`).

2. Make sure `pytest` is installed in the Python environment used by FreeCAD.
   You can usually install it by running:

   ```
   FreeCADCmd -c "import sys, subprocess; subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pytest'])"
   ```

3. From the SquatchCut repository root, run:

   ```
   FreeCADCmd -c "import run_freecad_tests"
   ```

   This will run all tests in `tests_integration/`.

   On macOS with the official FreeCAD .app, `FreeCADCmd` is typically located at:

   ```
   /Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd
   ```

   So you can run:

   ```
   /Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd -c "import run_freecad_tests"
   ```

---

## 🤝 Contributing

This project is intended to grow over time with:

- Curved nesting  
- Grain-direction-aware optimization  
- True GUI-previews of nesting  
- Plugin settings pages  
- Export templates (DXF, SVG)  
- Bookmatching  
- Optimizing based on material types  
- And more…

Contributions should follow the architecture documented in:
- `docs/architecture.md`
- `docs/mvp.md`
- `docs/codex_workflows.md`

---

## 🦶 Why “SquatchCut”?

Because everything is better with a little Sasquatch energy.  
And this tool is built to be:

- Simple  
- Powerful  
- Hard to kill  
- And leaves massive footprints in your workflow  
