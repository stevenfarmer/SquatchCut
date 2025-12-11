from hypothesis import assume, given, strategies as st
import pytest

from SquatchCut.core.units import (
    format_imperial_length,
    inches_to_mm,
    mm_to_inches,
    parse_imperial_inches,
)


finite_mm_values = st.floats(
    min_value=0.1,
    max_value=10000.0,
    allow_nan=False,
    allow_infinity=False,
)


@st.composite
def fractional_inches(draw):
    base_inches = draw(st.integers(min_value=0, max_value=120))
    denominator = draw(st.sampled_from((8, 16, 32)))
    numerator = draw(st.integers(min_value=0, max_value=denominator))
    fraction = numerator / float(denominator)
    return base_inches + fraction, denominator


@given(mm_value=finite_mm_values)
def test_mm_to_inches_round_trip(mm_value):
    inches = mm_to_inches(mm_value)
    mm_back = inches_to_mm(inches)
    assert abs(mm_back - float(mm_value)) <= 1e-6


@given(pair=st.tuples(finite_mm_values, finite_mm_values))
def test_mm_to_inches_monotonic(pair):
    lower, upper = pair
    assume(upper > lower + 1e-6)
    inches_lower = mm_to_inches(lower)
    inches_upper = mm_to_inches(upper)
    assert inches_upper > inches_lower


@given(
    mm_value=finite_mm_values,
    factor=st.floats(min_value=1.1, max_value=5.0, allow_nan=False, allow_infinity=False),
)
def test_mm_scaling_preserves_ratio(mm_value, factor):
    base_inches = mm_to_inches(mm_value)
    scaled_inches = mm_to_inches(mm_value * factor)
    assert scaled_inches >= base_inches
    assert scaled_inches == pytest.approx(base_inches * factor, rel=1e-9, abs=1e-6)


@given(value_and_denominator=fractional_inches())
def test_fractional_formatting_round_trip(value_and_denominator):
    inches_value, denominator = value_and_denominator
    mm_value = inches_to_mm(inches_value)
    formatted = format_imperial_length(mm_value, max_denominator=denominator)
    parsed_inches = parse_imperial_inches(formatted)
    assert formatted
    assert parsed_inches == pytest.approx(inches_value, abs=1e-4)
