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
- CSV import for panel lists  
- User-configurable sheet size + kerf  
- Multi-sheet rectangular nesting (Skyline / Guillotine hybrid)  
- Generate 2D panel layout geometry per sheet  
- Export PDF + CSV nesting reports  
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

### **4. Export Report**
Choose a directory → PDF + CSV written there.

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
