# Codex Automation Workflows

**Note:** Codex operates as the implementation agent under the direction of Jules (Lead Developer) and Architect (Spec Owner). See `AGENTS.md` for the full protocol.

## Overview
- This repository uses @codex headers in each module to guide incremental development.
- Each module documents its own responsibility, boundaries, and expectations to keep changes targeted.

## Global Codex Commands

1. `@codex implement next core logic`
   - Codex should examine method stubs in core modules and fill in the next unimplemented piece.

2. `@codex update feature <X>`
   - Codex should locate the correct module(s) using headers, update logic, and avoid touching unrelated modules.

3. `@codex refactor safely`
   - Codex should refactor only the module containing the comment without changing structure or deleting headers.

4. `@codex sync architecture`
   - Codex should compare code with docs/architecture.md and fix inconsistencies.

5. `@codex integrate GUI`
   - Codex should update dialogs and commands to work with the current state of the core logic.

6. `@codex implementation status`
   - Codex should scan headers and list which modules have remaining TODO implementations.

## Rules for Codex
- Do not overwrite files.
- Only modify sections relevant to the active module.
- Follow @codex header expectations.
- Preserve docstrings and method signatures.
- Never introduce cross-module logic.
