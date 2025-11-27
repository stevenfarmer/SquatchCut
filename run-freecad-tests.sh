#!/usr/bin/env bash
# @codex
# File: run-freecad-tests.sh
# Summary: Runs SquatchCut FreeCAD integration tests via FreeCADCmd.
# Details:
#   - Locates FreeCADCmd (macOS app bundle or PATH).
#   - Executes run_freecad_tests.py with pytest on tests_integration.
set -e

# Detect typical FreeCADCmd locations
if [ -x "/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd" ]; then
    FREECAD_CMD="/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd"
elif command -v FreeCADCmd >/devnull 2>&1; then
    FREECAD_CMD="$(command -v FreeCADCmd)"
else
    echo "ERROR: Could not find FreeCADCmd. Install FreeCAD or update run-freecad-tests.sh."
    exit 1
fi

echo "Running SquatchCut FreeCAD integration tests with: $FREECAD_CMD"
"$FREECAD_CMD" -c "import run_freecad_tests"
