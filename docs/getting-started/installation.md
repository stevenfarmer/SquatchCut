# Installation

## Requirements
- FreeCAD (recent stable release)
- Python (for running tests inside FreeCAD environment)
- Node.js and npm (for ts-tools)

## Installing the SquatchCut workbench
1. Clone this repository into FreeCAD's Mod directory:
   - Linux/macOS: `~/.local/share/FreeCAD/Mod/`
   - Windows: `%APPDATA%\FreeCAD\Mod\`
2. Restart FreeCAD.
3. Choose **SquatchCut** from the Workbench dropdown.

## Installing ts-tools
```bash
cd ts-tools
npm install
npm run build
```
