import csv

from SquatchCut.core.csv_import import validate_csv_file


def _write_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def test_validate_csv_valid(tmp_path):
    path = tmp_path / "valid.csv"
    header = ["id", "width", "height", "qty", "label", "material", "allow_rotate"]
    rows = [
        {"id": "P1", "width": "100", "height": "200", "qty": "2", "label": "Panel1", "material": "Oak", "allow_rotate": "yes"},
        {"id": "P2", "width": "50", "height": "80", "qty": "1", "label": "Panel2", "material": "Pine", "allow_rotate": "no"},
    ]
    _write_csv(path, header, rows)
    parts, errors = validate_csv_file(path, csv_units="metric")
    assert not errors
    assert len(parts) == 2
    assert parts[0]["qty"] == 2
    assert parts[0]["allow_rotate"] is True
    assert parts[1]["allow_rotate"] is False


def test_validate_csv_missing_headers(tmp_path):
    path = tmp_path / "missing_headers.csv"
    header = ["id", "width"]  # missing height
    _write_csv(path, header, [{"id": "P1", "width": "100"}])
    parts, errors = validate_csv_file(path)
    assert parts == []
    assert len(errors) == 1
    assert "Missing required column" in errors[0].message


def test_validate_csv_invalid_values(tmp_path):
    path = tmp_path / "invalid_values.csv"
    header = ["id", "width", "height", "qty"]
    rows = [
        {"id": "P1", "width": "-10", "height": "20", "qty": "1"},
        {"id": "P2", "width": "10", "height": "abc", "qty": "1"},
        {"id": "P3", "width": "30", "height": "40", "qty": "0"},
    ]
    _write_csv(path, header, rows)
    parts, errors = validate_csv_file(path)
    assert parts == []
    assert len(errors) == 3
    assert any("Width must be greater than zero" in err.message for err in errors)
    assert any("must be a number" in err.message.lower() for err in errors)


def test_validate_csv_mixed_rows(tmp_path):
    path = tmp_path / "mixed.csv"
    header = ["id", "width", "height"]
    rows = [
        {"id": "P1", "width": "50", "height": "60"},
        {"id": "P2", "width": "0", "height": "20"},
        {"id": "P3", "width": "70", "height": "80"},
    ]
    _write_csv(path, header, rows)
    parts, errors = validate_csv_file(path)
    assert parts == []
    assert len(errors) == 1
    assert errors[0].row == 3


def test_validate_csv_ignores_blank_rows(tmp_path):
    path = tmp_path / "blank_rows.csv"
    header = ["id", "width", "height"]
    rows = [
        {"id": "P1", "width": "10", "height": "20"},
        {"id": "", "width": "", "height": ""},
        {"id": "P2", "width": "30", "height": "40"},
    ]
    _write_csv(path, header, rows)
    parts, errors = validate_csv_file(path)
    assert not errors
    assert len(parts) == 2
