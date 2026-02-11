# CI/CD Reliability Checklist

This project relies on three GitHub Actions flows:

| Workflow | Responsibility | Trigger |
| --- | --- | --- |
| **Tests** (`tests.yml`) | Install `requirements-dev.txt`, run `ruff` and the pytest suite under `PYTHONPATH=freecad` with coverage | push/pull_request to `main`/`master` |
| **Docs** (`docs.yml`) | Build the MkDocs site with `mkdocs-material` and publish the generated `site/` directory to GitHub Pages | push to `main` (PRs build but don’t deploy) |
| **Ruff autofix** (`ruff-autofix.yml`) | Manual `workflow_dispatch` that installs `requirements-dev.txt`, runs `ruff check . --fix`, stages all files, and pushes the autofix commit | manual trigger |
| **Pre-commit check** (`precommit-check.yml`) | Create `.venv` and run `scripts/precommit-check.sh` (installs dev deps, then runs `ruff check .` and the coverage-aware pytest suite) | push/pull_request to `main`/`master` |

## General requirements to keep the pipeline green

1. **Match runner Python**: GitHub Actions currently uses Python 3.11 for the tests job. Locally, run the tests with `python3.11` (or the provided `.venv`) so you catch compatibility issues before committing.
2. **Install dev dependencies**:
   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements-dev.txt
   ```
   Keep `requirements-dev.txt` up to date whenever you add tools used by CI (pytest, ruff, hypothesis, mypy, etc.).
3. **Lint locally before pushing**:
   ```bash
   ruff check .
   ```
   The tests job runs `ruff check .` as well; any new violations will fail CI immediately.
4. **Type check the core package**:
   ```bash
   PYTHONPATH=freecad mypy freecad/SquatchCut
   ```
   The CI job mirrors this command and relies on the `pyproject.toml` configuration so you can catch typing issues before opening a PR.
5. **Automate lint + tests via pre-commit**:
   1. Activate the `.venv`: `source .venv/bin/activate`.
   2. Install the git hook (once per clone): `.venv/bin/pre-commit install`.
   3. On every commit the hook runs `scripts/precommit-check.sh`, which installs dev deps inside the venv, runs `ruff check .`, runs `mypy freecad/SquatchCut`, and executes the full pytest suite with the CI coverage flags. That way the same errors surface locally before pushing.
   The `precommit-check.yml` workflow mirrors `scripts/precommit-check.sh` inside a CI `.venv` on pushes/PRs to `main`/`master`, so the same pip install + lint/test combo fails early.
6. **Run the full test suite locally** (or at least the critical slices) before pushing:
   ```bash
   PYTHONPATH=freecad python -m pytest --cov=SquatchCut.core.nesting --cov=SquatchCut.core.session_state
   ```
   Keep coverage-sensitive files (`SquatchCut/core/nesting.py`, `session_state.py`) exercised so the `--cov-fail-under=80` threshold stays satisfied.
7. **Rebuild docs if you edit the MkDocs sources**:
   ```bash
   python -m pip install mkdocs mkdocs-material
   mkdocs build --strict
   ```
   A strict build means every reference, include, and navigation entry must be valid or the docs workflow will fail.

## Cache strategy

- The tests job caches `~/.cache/pip` with a key derived from `requirements-dev.txt`. If you edit `requirements-dev.txt`, cache misses will force re-installs.
- The docs job caches the same pip cache keyed on `mkdocs.yml`, so add documentation dependencies there only when necessary.
- If the cache ever becomes corrupt (CI keeps using stale packages), rerun the workflow with the **Clear cache** button (or change the cache key by modifying the hashed file).

## Troubleshooting Common Failures

- **`python -m pip install` fails**: Retry the workflow; transient network issues are common. For persistent issues, check `pip` output and mirror usage.
- **`ruff check .` fails**: Fix the lint violation locally, rerun `ruff check .`, then recommit. The Ruff autofix workflow is available if manual fixes become repetitive.
- **`pytest` coverage fails**: Look for missing imports, new modules without tests, or tests that take too long and time out. Run the local coverage command above to inspect the report.
- **`mkdocs build --strict` fails**: Ensure every reference, link, and include is valid. Use `mkdocs build --strict` locally before pushing documentation changes.

## Best practices

- Run the test+lint suite locally in the same environment (the provided `.venv` or Python 3.11) before pushing to reduce CI noise.
- When adding dependencies, update `requirements-dev.txt` and rerun `pip install -r requirements-dev.txt`. Don’t rely on the cached wheel if the dependency lacks a wheel for 3.11—CI will download the source wheel but may take longer.
- If you change MkDocs config (nav, theme, metadata), rebuild the site locally to catch strict mode issues early.
- Use the `Ruff autofix` workflow only when you trust the auto-fixes; manual review is still required before merging.

Keeping these requirements satisfied will minimize failing GitHub Actions runs and save everyone from repeated noisy reruns.
