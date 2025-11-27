/* @codex
 * Purpose: Shared panel type definitions for preprocessing and validation.
 * Pipeline: Imported by validation and preprocessing steps to ensure consistent shapes.
 * Exports: Panel, PanelInputRow; does not import runtime-heavy dependencies.
 * Note: TS logic must remain pure and framework-independent.
 */

export interface Panel {
  id: string;
  width: number;
  height: number;
  grainDirection?: string;
  rotationAllowed?: boolean;
}

export interface PanelInputRow {
  [key: string]: unknown;
}

export interface ValidationResult {
  panels: Panel[];
  errors: string[];
}
