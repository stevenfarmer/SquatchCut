from pathlib import Path

from SquatchCut.core.csv_loader import load_csv, in_to_mm


def _load(path, units):
    return load_csv(str(path), csv_units=units)


def test_metric_and_imperial_csv_equivalence_small():
    base = Path("freecad/testing/csv")
    metric = _load(base / "valid_panels_small.csv", "metric")
    imperial = _load(base / "valid_panels_small_imperial.csv", "imperial")

    assert len(metric) == len(imperial)
    for m, i in zip(metric, imperial):
        assert m["id"] == i["id"]
        assert abs(m["width"] - i["width"]) < 1e-2
        assert abs(m["height"] - i["height"]) < 1e-2


def test_imperial_csv_misread_as_metric_differs():
    base = Path("freecad/testing/csv")
    metric = _load(base / "valid_panels_small.csv", "metric")
    imperial_wrong = _load(base / "valid_panels_small_imperial.csv", "metric")

    assert len(metric) == len(imperial_wrong)
    mismatches = 0
    for m, i in zip(metric, imperial_wrong):
        if abs(m["width"] - i["width"]) > 1e-3 or abs(m["height"] - i["height"]) > 1e-3:
            mismatches += 1
    assert mismatches > 0


def test_in_to_mm():
    assert abs(in_to_mm(1.0) - 25.4) < 1e-6
