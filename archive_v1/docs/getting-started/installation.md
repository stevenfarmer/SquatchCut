# Installation

## Requirements
- FreeCAD 0.21+ (current stable release)
- Python (only if you plan to run the pytest suite)
- Node.js and npm (only if you want to build/use ts-tools)

## Install via FreeCAD Add-on Manager (recommended)
1. Open **FreeCAD**.
2. Go to **Tools → Add-on Manager → Install from ZIP**.
3. Select the SquatchCut ZIP you received or downloaded.
4. Restart FreeCAD.
5. Choose **SquatchCut** from the Workbench dropdown.

## Developer checkout (optional)
If you need a live checkout instead of a ZIP:
1. Clone this repository into FreeCAD's Mod directory:
   - Linux/macOS: `~/.local/share/FreeCAD/Mod/`
   - Windows: `%APPDATA%\\FreeCAD\\Mod\\`
2. Restart FreeCAD.
3. Choose **SquatchCut** from the Workbench dropdown.

## Installing ts-tools (optional helper for CSV validation)
```bash
cd ts-tools
npm install
npm run build
```
