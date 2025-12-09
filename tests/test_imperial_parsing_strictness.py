import pytest
from SquatchCut.core.units import parse_imperial_inches

def test_strict_parsing_rejects_malformed_dashes():
    """
    Ensure that trailing dashes, leading dashes, or multiple dashes
    that don't form valid imperial measurements are rejected.
    """
    invalid_inputs = [
        "5-",
        "-5",
        "5 -",
        " - 5",
        "5--1/2",
        "5 - - 1/2",
        "-",
        " - ",
    ]
    for inp in invalid_inputs:
        with pytest.raises(ValueError, match="Invalid imperial length format"):
            parse_imperial_inches(inp)

def test_strict_parsing_accepts_valid_inputs():
    """
    Ensure valid inputs are still accepted.
    """
    valid_cases = {
        "48": 48.0,
        "48.5": 48.5,
        "3/4": 0.75,
        "48 3/4": 48.75,
        "48-3/4": 48.75,
        "48 - 3/4": 48.75,
        "  48  -  3/4  ": 48.75,
    }
    for inp, expected in valid_cases.items():
        assert parse_imperial_inches(inp) == pytest.approx(expected, 1e-6)
