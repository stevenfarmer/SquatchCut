#!/usr/bin/env node
/* @codex
 * Purpose: Simple CLI to validate and preprocess panel CSV files.
 * Pipeline: Reads CSV, validates rows, preprocesses panels, and reports summary.
 * Imports/Exports: Uses loadAndPreprocessCSV from index; no FreeCAD dependencies.
 * Note: TS logic must remain pure and framework-independent.
 */

import { loadAndPreprocessCSV } from "./index";

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length < 1) {
    console.error("Usage: squatchcut-csv <path/to/panels.csv>");
    process.exit(1);
  }

  const csvPath = argv[0];
  try {
    const result = await loadAndPreprocessCSV(csvPath);
    if (result.errors.length > 0) {
      result.errors.forEach((err) => console.error(`ERROR: ${err}`));
    }
    console.log(
      `Panels loaded: ${result.panels.length}, Errors: ${result.errors.length}`,
    );
    if (result.panels.length > 0) {
      const preview = result.panels.slice(0, 3);
      console.log("Preview:", JSON.stringify(preview, null, 2));
    }
    process.exit(0);
  } catch (err) {
    console.error(`Failed to read or process CSV: ${err}`);
    process.exit(1);
  }
}

void main();
