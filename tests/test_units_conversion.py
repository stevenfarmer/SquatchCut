from SquatchCut.core import session_state
from SquatchCut.core.units import inches_to_mm, mm_to_inches


def test_mm_to_inches_and_back():
    assert mm_to_inches(25.4) == 1.0
    assert inches_to_mm(1.0) == 25.4
    val_mm = 123.4
    assert abs(inches_to_mm(mm_to_inches(val_mm)) - val_mm) < 1e-6


def test_measurement_system_roundtrip():
    # default should be metric
    session_state.set_measurement_system("metric")
    assert session_state.get_measurement_system() == "metric"
    session_state.set_measurement_system("imperial")
    assert session_state.get_measurement_system() == "imperial"
    session_state.set_measurement_system("metric")
    assert session_state.get_measurement_system() == "metric"
