from SquatchCut.core.units import (
    format_imperial_length,
    inches_to_mm,
    parse_imperial_inches,
)


def test_parse_imperial_formats():
    assert parse_imperial_inches("48") == 48.0
    assert parse_imperial_inches("48.5") == 48.5
    assert parse_imperial_inches("3/4") == 0.75
    assert parse_imperial_inches("48 3/4") == 48.75
    assert parse_imperial_inches("48-3/4") == 48.75
    assert parse_imperial_inches(" 48  -  3/4 ") == 48.75


def test_parse_imperial_invalid():
    import pytest

    with pytest.raises(ValueError):
        parse_imperial_inches("foo")
    with pytest.raises(ValueError):
        parse_imperial_inches("48 /")
    with pytest.raises(ValueError):
        parse_imperial_inches("48 3/0")


def test_format_imperial_examples():
    assert format_imperial_length(inches_to_mm(48.0)) == "48"
    assert format_imperial_length(inches_to_mm(48.25)) == "48 1/4"
    assert format_imperial_length(inches_to_mm(48.5)) == "48 1/2"
    assert format_imperial_length(inches_to_mm(48.75)) == "48 3/4"
    assert format_imperial_length(inches_to_mm(0.75)) == "3/4"


def test_format_parse_roundtrip():
    values = [48.0, 48.25, 48.5, 48.75, 12.125]
    for inches in values:
        mm_value = inches_to_mm(inches)
        string = format_imperial_length(mm_value)
        parsed = parse_imperial_inches(string)
        assert abs(parsed - inches) < 1e-6
