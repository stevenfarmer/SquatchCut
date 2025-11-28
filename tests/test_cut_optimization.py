"""Tests for guillotine-style cut optimization nesting."""

from SquatchCut.core.nesting import Part, NestingConfig, nest_parts
from SquatchCut.core.cut_optimization import guillotine_nest_parts


def _rects_overlap(a, b):
    if a.sheet_index != b.sheet_index:
        return False
    ax1, ay1, ax2, ay2 = a.x, a.y, a.x + a.width, a.y + a.height
    bx1, by1, bx2, by2 = b.x, b.y, b.x + b.width, b.y + b.height
    if ax2 <= bx1 or bx2 <= ax1:
        return False
    if ay2 <= by1 or by2 <= ay1:
        return False
    return True


def _within_sheet(p, w, h):
    return p.x >= 0 and p.y >= 0 and (p.x + p.width) <= w + 1e-6 and (p.y + p.height) <= h + 1e-6


def test_guillotine_nest_no_overlap():
    parts = [
        Part(id="a", width=100, height=80),
        Part(id="b", width=80, height=60),
        Part(id="c", width=50, height=50),
    ]
    sheet = {"width": 300, "height": 200}
    placed = guillotine_nest_parts(parts, sheet, NestingConfig(optimize_for_cut_path=True))

    assert len(placed) == len(parts)
    for i in range(len(placed)):
        assert _within_sheet(placed[i], sheet["width"], sheet["height"])
        for j in range(i + 1, len(placed)):
            assert not _rects_overlap(placed[i], placed[j])


def test_guillotine_respects_rotation_constraints():
    parts = [
        Part(id="tall", width=200, height=140, can_rotate=True),
    ]
    sheet = {"width": 150, "height": 220}
    cfg = NestingConfig(optimize_for_cut_path=True, allowed_rotations_deg=(0, 90))
    placed = guillotine_nest_parts(parts, sheet, cfg)

    assert placed[0].rotation_deg in (0, 90)
    assert _within_sheet(placed[0], sheet["width"], sheet["height"])

    cfg_no_rotate = NestingConfig(optimize_for_cut_path=True, allowed_rotations_deg=(0,))
    try:
        guillotine_nest_parts(parts, sheet, cfg_no_rotate)
        assert False, "Expected ValueError when rotation is disallowed for fitting part"
    except ValueError:
        pass


def test_guillotine_uses_kerf_spacing():
    parts = [
        Part(id="a", width=80, height=50),
        Part(id="b", width=80, height=50),
    ]
    sheet = {"width": 250, "height": 100}
    kerf = 10.0
    cfg = NestingConfig(optimize_for_cut_path=True, kerf_width_mm=kerf)
    placed = guillotine_nest_parts(parts, sheet, cfg)

    assert len(placed) == 2
    # Expect second part to be offset by at least width + kerf
    xs = sorted(p.x for p in placed)
    assert xs[1] - xs[0] >= parts[0].width + kerf - 1e-6


def test_nest_parts_respects_optimize_for_cut_path_flag():
    parts = [
        Part(id="a", width=50, height=50),
        Part(id="b", width=60, height=40),
    ]
    sheet_w = 200
    sheet_h = 200

    default_result = nest_parts(parts, sheet_w, sheet_h)
    assert len(default_result) == len(parts)

    cfg = NestingConfig(optimize_for_cut_path=True)
    cut_path_result = nest_parts(parts, sheet_w, sheet_h, cfg)
    assert len(cut_path_result) == len(parts)
    # Heuristic: placements differ when using guillotine vs default
    assert any(p.x != q.x or p.y != q.y for p, q in zip(default_result, cut_path_result))
