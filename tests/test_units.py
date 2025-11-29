from SquatchCut.core.units import (
    inches_to_fraction_str,
    format_length,
    parse_length,
    format_preset_label,
    unit_label_for_system,
    parse_imperial_inches,
)


def test_inches_to_fraction_str_basic():
    assert inches_to_fraction_str(1.0) == "1"
    assert inches_to_fraction_str(0.75) == "3/4"
    assert inches_to_fraction_str(1.75) == "1 3/4"
    assert inches_to_fraction_str(48.0) == "48"
    assert inches_to_fraction_str(48.125, max_denominator=16) == "48 1/8"
    assert inches_to_fraction_str(0.2499, max_denominator=16) == "1/4"


def test_parse_imperial_inches_formats():
    assert parse_imperial_inches("48") == 48.0
    assert parse_imperial_inches("48.5") == 48.5
    assert parse_imperial_inches("3/4") == 0.75
    assert parse_imperial_inches("48 3/4") == 48.75
    assert parse_imperial_inches("48-3/4") == 48.75
    assert parse_imperial_inches("  48  -  3/4 ") == 48.75


def test_parse_fraction_round_trip():
    values = [0.5, 0.75, 1.25, 23.375]
    for v in values:
        s = inches_to_fraction_str(v, max_denominator=16)
        v2 = parse_imperial_inches(s)
        assert abs(v - v2) < 1e-6


def test_format_length_metric_and_imperial():
    assert format_length(25.4, "metric") == "25.4"
    assert format_length(25.4, "imperial") == "1"
    assert format_length(53.975, "imperial") == "2 1/8"  # 2.125 in


def test_parse_length_metric_and_imperial():
    assert parse_length("1220", "metric") == 1220.0
    mm_val = parse_length("48 1/8", "imperial")
    assert abs(mm_val - 1222.375) < 1e-3  # 48.125 in to mm


def test_format_preset_label_respects_system():
    metric_label = format_preset_label(1220, 2440, "metric", nickname="4x8 ft")
    assert metric_label.startswith("1220 x 2440 mm")
    assert "4x8 ft" in metric_label

    imperial_label = format_preset_label(1220, 2440, "imperial", nickname="4x8 ft")
    assert imperial_label.startswith("48")
    assert "in" in imperial_label.split("(", 1)[0]
    assert "1220 x 2440 mm" in imperial_label
    assert "4x8 ft" in imperial_label


def test_unit_label_for_system():
    assert unit_label_for_system("metric") == "mm"
    assert unit_label_for_system("imperial") == "in"


def test_parse_length_empty_raises():
    import pytest

    with pytest.raises(ValueError):
        parse_length("", "metric")

