from hypothesis import given, settings, strategies as st

from SquatchCut.core.nesting import NestingConfig, Part, nest_parts
from SquatchCut.core.nesting_engine import NestingEngine
from SquatchCut.core.overlap_check import detect_overlaps


dimension_strategy = st.floats(
    min_value=200.0,
    max_value=2500.0,
    allow_nan=False,
    allow_infinity=False,
)


@st.composite
def guillotine_inputs(draw):
    sheet_width = draw(dimension_strategy)
    sheet_height = draw(dimension_strategy)
    kerf = draw(st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False))
    part_count = draw(st.integers(min_value=1, max_value=12))
    parts = []
    for idx in range(part_count):
        max_width = max(20.0, sheet_width * 0.5)
        max_height = max(20.0, sheet_height * 0.5)
        width = draw(st.floats(min_value=10.0, max_value=max_width, allow_nan=False, allow_infinity=False))
        height = draw(st.floats(min_value=10.0, max_value=max_height, allow_nan=False, allow_infinity=False))
        parts.append(
            Part(
                id=f"part-{idx}",
                width=width,
                height=height,
                can_rotate=draw(st.booleans()),
            )
        )
    return sheet_width, sheet_height, kerf, parts


@st.composite
def skyline_inputs(draw):
    sheet_width = draw(st.floats(min_value=200.0, max_value=1500.0, allow_nan=False, allow_infinity=False))
    sheet_height = draw(st.floats(min_value=200.0, max_value=1500.0, allow_nan=False, allow_infinity=False))
    panel_count = draw(st.integers(min_value=1, max_value=3))
    panels = []
    for idx in range(panel_count):
        min_width = max(40.0, sheet_width * 0.2)
        min_height = max(40.0, sheet_height * 0.2)
        max_width = max(min_width, sheet_width * 0.6)
        max_height = max(min_height, sheet_height * 0.6)
        width = draw(st.floats(min_value=min_width, max_value=max_width, allow_nan=False, allow_infinity=False))
        height = draw(st.floats(min_value=min_height, max_value=max_height, allow_nan=False, allow_infinity=False))
        panels.append(
            {
                "id": f"panel-{idx}",
                "width": width,
                "height": height,
                "rotation_allowed": draw(st.booleans()),
            }
        )
    return sheet_width, sheet_height, panels


def _dicts_overlap(a, b, epsilon=1e-6):
    ax2 = a["x"] + a["width"]
    ay2 = a["y"] + a["height"]
    bx2 = b["x"] + b["width"]
    by2 = b["y"] + b["height"]
    return (
        a["x"] < bx2 - epsilon
        and ax2 > b["x"] + epsilon
        and a["y"] < by2 - epsilon
        and ay2 > b["y"] + epsilon
    )


@given(guillotine_inputs())
@settings(max_examples=25)
def test_guillotine_nesting_has_no_overlaps_and_stays_in_bounds(scenario):
    sheet_width, sheet_height, kerf, parts = scenario
    config = NestingConfig(optimize_for_cut_path=True, kerf_width_mm=kerf)
    placements = nest_parts(parts, sheet_width, sheet_height, config=config)

    assert len(placements) <= len(parts)
    assert not detect_overlaps(placements)

    placed_ids = [p.id for p in placements]
    assert len(placed_ids) == len(set(placed_ids))
    assert set(placed_ids).issubset({p.id for p in parts})

    for placement in placements:
        assert placement.x >= -1e-6
        assert placement.y >= -1e-6
        assert placement.x + placement.width <= sheet_width + 1e-6
        assert placement.y + placement.height <= sheet_height + 1e-6


@given(skyline_inputs())
@settings(max_examples=25)
def test_nesting_engine_placements_do_not_overlap(scenario):
    sheet_width, sheet_height, panels = scenario
    engine = NestingEngine()
    placements, _ = engine.nest_panels(panels, sheet_width, sheet_height)

    ids = [p.get("panel_id") for p in placements]
    assert len(ids) == len(set(ids))
    assert set(ids).issubset({p["id"] for p in panels})

    for placement in placements:
        assert placement["x"] >= 0.0
        assert placement["y"] >= 0.0
        assert placement["x"] + placement["width"] <= sheet_width + 1e-6
        assert placement["y"] + placement["height"] <= sheet_height + 1e-6

    for i in range(len(placements)):
        for j in range(i + 1, len(placements)):
            assert not _dicts_overlap(placements[i], placements[j])
