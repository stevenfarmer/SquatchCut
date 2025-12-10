from __future__ import annotations

import pathlib

DOCS_DIR = pathlib.Path(__file__).resolve().parents[1] / "docs"
PROJECT_GUIDE = DOCS_DIR / "Project_Guide_v3.2.md"
BACKLOG_DOC = DOCS_DIR / "Backlog.md"


def read_file(path: pathlib.Path) -> str:
    """Return file contents or raise an assertion if missing."""
    assert path.exists(), f"Expected documentation file {path} to exist."
    return path.read_text(encoding="utf-8")


def test_project_guide_has_status_snapshot_section():
    guide = read_file(PROJECT_GUIDE)
    guide_upper = guide.upper()
    assert (
        "STATUS SNAPSHOT (DEC 2025)" in guide_upper
    ), "Expected 'STATUS SNAPSHOT (DEC 2025)' anchor in Project_Guide_v3.2.md."
    assert (
        "BACKLOG ALIGNMENT" in guide_upper
    ), "Expected Backlog Alignment heading in Project_Guide_v3.2.md."


def test_project_guide_does_not_reference_old_backlog_alignment_label():
    guide = read_file(PROJECT_GUIDE)
    old_label = "Backlog Alignment (Post–Nesting Fix Updates)"
    assert (
        old_label not in guide
    ), "Old backlog alignment label still present; v3.2 doc not fully updated."


def test_backlog_file_has_required_sections():
    backlog = read_file(BACKLOG_DOC)
    required_headers = [
        "Completed Since v3.2",
        "Active Backlog (High Priority)",
        "Future / Longer-Term Items",
    ]
    for header in required_headers:
        assert (
            header in backlog
        ), f"Missing backlog section header '{header}' in docs/Backlog.md."


def test_backlog_active_section_contains_key_items():
    backlog = read_file(BACKLOG_DOC)
    key_phrases = [
        "Preview Determinism",
        "TaskPanel Overflow",
        "Multi-Sheet Visualization",
        "Cut-Friendly Multi-Sheet",
        "Test Suite Expansion",
        "CSV Export & Cutlist",
        "Warning Banner Lifecycle",
        "Sheet Exhaustion Metrics",
    ]
    missing = [phrase for phrase in key_phrases if phrase not in backlog]
    assert not missing, f"Missing expected active backlog items: {missing}"


def test_backlog_future_section_contains_future_items():
    backlog = read_file(BACKLOG_DOC)
    future_phrases = [
        "cut-order visualization",
        "Multi-Sheet Presets",
        "Kerf Simulation",
    ]
    missing = [phrase for phrase in future_phrases if phrase not in backlog]
    assert not missing, f"Missing expected future backlog items: {missing}"
