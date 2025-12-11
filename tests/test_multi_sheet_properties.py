from hypothesis import given, settings, strategies as st

from SquatchCut.core.multi_sheet_optimizer import MultiSheetOptimizer


sheet_dimension = st.floats(
    min_value=300.0,
    max_value=2000.0,
    allow_nan=False,
    allow_infinity=False,
)


@st.composite
def sheet_and_panels(draw):
    sheet_width = draw(sheet_dimension)
    sheet_height = draw(sheet_dimension)
    panel_count = draw(st.integers(min_value=1, max_value=25))
    panels = []
    for idx in range(panel_count):
        max_width = max(40.0, sheet_width * 0.8)
        max_height = max(40.0, sheet_height * 0.8)
        width = draw(st.floats(min_value=20.0, max_value=max_width, allow_nan=False, allow_infinity=False))
        height = draw(st.floats(min_value=20.0, max_value=max_height, allow_nan=False, allow_infinity=False))
        panels.append({"id": f"panel-{idx}", "width": width, "height": height})
    return {"width": sheet_width, "height": sheet_height}, panels


@st.composite
def oversize_panels(draw):
    sheet_width = draw(st.floats(min_value=300.0, max_value=1500.0, allow_nan=False, allow_infinity=False))
    sheet_height = draw(st.floats(min_value=300.0, max_value=1500.0, allow_nan=False, allow_infinity=False))
    oversize_width = draw(st.floats(min_value=5.0, max_value=sheet_width, allow_nan=False, allow_infinity=False))
    oversize_height = draw(st.floats(min_value=5.0, max_value=sheet_height, allow_nan=False, allow_infinity=False))
    panels = [
        {
            "id": "oversize",
            "width": sheet_width + oversize_width,
            "height": sheet_height + oversize_height,
        }
    ]
    fit_count = draw(st.integers(min_value=1, max_value=8))
    for idx in range(fit_count):
        width = draw(st.floats(min_value=30.0, max_value=sheet_width * 0.7, allow_nan=False, allow_infinity=False))
        height = draw(st.floats(min_value=30.0, max_value=sheet_height * 0.7, allow_nan=False, allow_infinity=False))
        panels.append({"id": f"fit-{idx}", "width": width, "height": height})
    return {"width": sheet_width, "height": sheet_height}, panels


def _all_placements(sheets):
    for sheet in sheets:
        for placement in sheet.get("placements", []):
            yield sheet, placement


@given(sheet_and_panels())
@settings(max_examples=25)
def test_multi_sheet_allocation_conserves_and_deduplicates_ids(scenario):
    sheet_size, panels = scenario
    optimizer = MultiSheetOptimizer()
    sheets = optimizer.optimize(panels, sheet_size)

    input_ids = {panel["id"] for panel in panels}
    assigned_ids = []
    sheet_ids = [sheet.get("sheet_id") for sheet in sheets]

    if sheets:
        assert sheet_ids == list(range(1, len(sheets) + 1))

    for sheet, placement in _all_placements(sheets):
        assigned_ids.append(placement.get("panel_id"))
        assert placement["x"] >= 0.0
        assert placement["y"] >= 0.0
        assert placement["x"] + placement["width"] <= sheet["width"] + 1e-6
        assert placement["y"] + placement["height"] <= sheet["height"] + 1e-6

    assert set(assigned_ids).issubset(input_ids)
    assert len(assigned_ids) == len(set(assigned_ids))


@given(oversize_panels())
@settings(max_examples=25)
def test_oversized_panels_are_not_assigned(scenario):
    sheet_size, panels = scenario
    optimizer = MultiSheetOptimizer()
    sheets = optimizer.optimize(panels, sheet_size)

    assigned_ids = {placement.get("panel_id") for _sheet, placement in _all_placements(sheets)}
    assert "oversize" not in assigned_ids

    for sheet, placement in _all_placements(sheets):
        assert placement["x"] >= 0.0
        assert placement["y"] >= 0.0
        assert placement["x"] + placement["width"] <= sheet["width"] + 1e-6
        assert placement["y"] + placement["height"] <= sheet["height"] + 1e-6
