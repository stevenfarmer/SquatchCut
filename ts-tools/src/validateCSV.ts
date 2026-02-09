/* @codex
 * Purpose: Validate CSV input and produce normalized panels.
 * Pipeline: Consumes file paths, uses panel types, and feeds preprocess steps.
 * Imports/Exports: Import Panel; export validateCSV for upstream tooling.
 * Note: TS logic must remain pure and framework-independent.
 */

import * as fs from "fs";
import * as path from "path";
import { Panel, ValidationResult } from "./panelTypes";

/**
 * TODO: Validate CSV input and return normalized panels.
 */
export async function validateCSV(filePath: string): Promise<ValidationResult> {
  const absolutePath = path.resolve(filePath);
  const content = await fs.promises.readFile(absolutePath, "utf-8");

  const lines = content
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);

  const panels: Panel[] = [];
  const errors: string[] = [];

  if (lines.length === 0) {
    return { panels, errors: ["Empty CSV file"] };
  }

  const headerLine = lines.shift() as string;
  const headers = headerLine.split(",").map((h) => h.trim());
  const headerIndex: Record<string, number> = {};
  headers.forEach((h, i) => {
    const key = h;
    headerIndex[key] = i;
  });

  lines.forEach((line, idx) => {
    const parts = line.split(",");
    const row: PanelInputRow = {};
    headers.forEach((h, i) => {
      row[h] = parts[i]?.trim();
    });

    const rowNum = idx + 2; // account for header

    const id = String(row["id"] ?? "").trim();
    const widthRaw = row["width"];
    const heightRaw = row["height"];

    const width = parseFloat(String(widthRaw));
    const height = parseFloat(String(heightRaw));

    if (!id) {
      errors.push(`Row ${rowNum}: Missing id`);
      return;
    }
    if (!Number.isFinite(width) || width <= 0) {
      errors.push(`Row ${rowNum}: Invalid width '${widthRaw}'`);
      return;
    }
    if (!Number.isFinite(height) || height <= 0) {
      errors.push(`Row ${rowNum}: Invalid height '${heightRaw}'`);
      return;
    }

    const panel: Panel = {
      id,
      width,
      height,
      rotationAllowed: true,
    };

    panels.push(panel);
  });

  return { panels, errors };
}
