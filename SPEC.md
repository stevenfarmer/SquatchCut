# V2 Kickoff Spec

## Bridge migration
- Update `gemini_bridge.py` to import `google.genai` and instantiate `genai.Client(api_key=GEMINI_API_KEY)` while keeping the existing `consult_architect` helper, chosen models, and output formatting.
- Maintain the Foreman-facing console messaging so running `python gemini_bridge.py` continues to print the architect response or the failure message when the key is missing.

## SAE defaults
- Introduce `params.py` to own SAE constants: `INCH_TO_MM`, `DEFAULT_UNITS = "imperial"`, helpers `inches_to_mm()`/`mm_to_inches()`, and the `SheetSize` dataclass with computed mm dimensions.
- Export `SAE_SHEET_SIZE`, `SAE_SHEET_SIZE_MM`, and `DEFAULT_SHEET_SIZE` so downstream modules hydrate sheet dimensions without scattering `48 x 96` literals.

## MVP fractional CSV confirmation
- Refer to `AGENTS.md` which mandates that “Unit Logic: Support both decimal (23.5) and fractional (23 1/2) string inputs from CSVs” whenever the CSV fallback path is used.
- Confirm that `archive_v1/docs/mvp.md` already states CSV is a fallback mode with width/height fields, validation rules, and the requirement to reject invalid values (ensuring the CSV path is already part of the locked MVP).
- Document in this spec that the MVP plan must continue supporting fractional CSV inputs for both validation and parsing (per AGENTS requirements) before closing this task.

## Acceptance
- `gemini_bridge.py` and `params.py` both pass syntax checks via `python -m compileall gemini_bridge.py params.py`.
- SPEC.md remains the central reference for the Foreman/Liaison on these three coordinated changes.
