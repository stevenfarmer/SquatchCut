/* @codex
 * Purpose: Preprocess panels (normalize/filter/enrich) before nesting.
 * Pipeline: Receives panels from validation and outputs ready-to-use panel data.
 * Imports/Exports: Import Panel; export preprocessPanels for downstream use.
 * Note: TS logic must remain pure and framework-independent.
 */

import { Panel } from "./panelTypes";

export function preprocessPanels(panels: Panel[]): Panel[] {
  const result: Panel[] = [];
  for (const panel of panels) {
    const id = (panel.id ?? "").trim();
    const width = Number(panel.width);
    const height = Number(panel.height);

    if (!id) {
      continue;
    }
    if (!Number.isFinite(width) || !Number.isFinite(height)) {
      continue;
    }
    if (width <= 0 || height <= 0) {
      continue;
    }

    result.push({
      ...panel,
      id,
      width,
      height,
    });
  }

  // Future transformations:
  // - Apply grouping/tags
  // - Deduplicate panels
  return result;
}
