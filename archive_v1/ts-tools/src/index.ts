/* @codex
 * Purpose: Entry point that re-exports SquatchCut TS preprocessing tools.
 * Pipeline: Connects validation and preprocessing for external callers.
 * Imports/Exports: Export validateCSV, preprocessPanels, and panel types; avoid adding runtime logic here.
 * Note: TS logic must remain pure and framework-independent.
 */

export { validateCSV } from "./validateCSV";
export { preprocessPanels } from "./preprocess";
export type { Panel, PanelInputRow, ValidationResult } from "./panelTypes";

import { validateCSV } from "./validateCSV";
import { preprocessPanels } from "./preprocess";
import { ValidationResult } from "./panelTypes";

export async function loadAndPreprocessCSV(
  filePath: string,
): Promise<ValidationResult> {
  const result = await validateCSV(filePath);
  if (result.panels.length === 0) {
    return result;
  }
  const processed = preprocessPanels(result.panels);
  return {
    panels: processed,
    errors: result.errors,
  };
}
