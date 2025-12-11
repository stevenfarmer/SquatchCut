# AI Automation Workflows (Codex-style prompts)

**Note:** These prompts are templates for any AI worker (e.g., Codex, VS Code assistants, hosted GitHub agents) operating under Architect direction. See `AGENTS.md` for the full protocol.

## Overview
- This repository uses @codex-style headers in modules to guide incremental development; AI workers may treat “codex” as a placeholder keyword.
- Each module documents its own responsibility, boundaries, and expectations to keep changes targeted.

## Global AI Worker Commands (examples)

1. `@codex implement next core logic`
   - AI worker should examine method stubs in core modules and fill in the next unimplemented piece.

2. `@codex update feature <X>`
   - AI worker should locate the correct module(s) using headers, update logic, and avoid touching unrelated modules.

3. `@codex refactor safely`
   - AI worker should refactor only the module containing the comment without changing structure or deleting headers.

4. `@codex sync architecture`
   - AI worker should compare code with docs/architecture.md and fix inconsistencies.

5. `@codex integrate GUI`
   - AI worker should update dialogs and commands to work with the current state of the core logic.

6. `@codex implementation status`
   - AI worker should scan headers and list which modules have remaining TODO implementations.

## Rules for AI workers using these prompts
- Do not overwrite files.
- Only modify sections relevant to the active module.
- Follow @codex header expectations.
- Preserve docstrings and method signatures.
- Never introduce cross-module logic.
