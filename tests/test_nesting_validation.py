import pytest

from SquatchCut.core.nesting import (
    NestingValidationError,
    get_usable_sheet_area,
    part_fits_sheet,
    validate_parts_fit_sheet,
    Part,
)


def test_get_usable_sheet_area_respects_margin():
    usable_width, usable_height = get_usable_sheet_area(1000, 500, margin_mm=10)
    assert pytest.approx(980.0) == usable_width
    assert pytest.approx(480.0) == usable_height


def test_part_fits_sheet_with_rotation():
    assert part_fits_sheet(800, 500, 609.6, 1219.2, can_rotate=True)
    assert not part_fits_sheet(800, 500, 609.6, 1219.2, can_rotate=False)
    assert part_fits_sheet(600, 600, 600, 600)


def test_validate_parts_fit_sheet_all_fit():
    usable_width, usable_height = get_usable_sheet_area(1000, 1000, margin_mm=0)
    parts = [
        Part(id="a", width=500, height=400),
        Part(id="b", width=600, height=600, can_rotate=True),
    ]
    # Should not raise
    validate_parts_fit_sheet(parts, usable_width, usable_height)


def test_validate_parts_fit_sheet_detects_oversize():
    usable_width, usable_height = get_usable_sheet_area(609.6, 1219.2, margin_mm=0)
    parts = [
        Part(id="p1", width=609.6, height=1219.2),
        Part(id="p2", width=800, height=500, can_rotate=True),
    ]
    # this should still pass because rotation allows fit
    validate_parts_fit_sheet(parts, usable_width, usable_height)

    # disallow rotate to trigger error
    parts[1].can_rotate = False
    with pytest.raises(NestingValidationError) as excinfo:
        validate_parts_fit_sheet(parts, usable_width, usable_height)
    error = excinfo.value
    assert error.offending_parts
    assert error.offending_parts[0].part_id == "p2"


def test_validate_parts_fit_sheet_reports_multiple_offenders():
    usable_width, usable_height = get_usable_sheet_area(100, 100, margin_mm=0)
    parts = [
        Part(id="too_wide", width=200, height=50),
        Part(id="too_tall", width=50, height=200),
    ]
    with pytest.raises(NestingValidationError) as excinfo:
        validate_parts_fit_sheet(parts, usable_width, usable_height)
    error = excinfo.value
    assert len(error.offending_parts) == 2
