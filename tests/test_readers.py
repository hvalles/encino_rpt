"""Tests de readers multi-formato (`Report.read` / `encino_rpt.readers`)."""

import io
import sys

import pytest

from encino_rpt import Report
from encino_rpt.readers import _coerce
from encino_rpt.readers import read as read_rows


# --- auto-detección de tipos (_coerce) ---
def test_coerce_scalars():
    assert _coerce("100") == 100
    assert _coerce("100.5") == 100.5
    assert _coerce("true") is True
    assert _coerce("false") is False
    assert _coerce("") is None
    assert _coerce("null") is None
    assert _coerce("none") is None
    assert _coerce("N/A") == "N/A"
    assert _coerce(5) == 5
    assert _coerce(None) is None


def test_coerce_non_finite_kept_as_str():
    assert _coerce("nan") == "nan"
    assert _coerce("NaN") == "NaN"
    assert _coerce("inf") == "inf"
    assert _coerce("-inf") == "-inf"
    assert _coerce("infinity") == "infinity"


# --- CSV ---
def test_read_csv_path(tmp_path):
    path = tmp_path / "datos.csv"
    path.write_text("nombre,monto\nAna,100\nBob,50\n", encoding="utf-8")

    result = Report.read(path).detail("nombre", "monto").run()

    assert result.columns == ["nombre", "monto"]
    assert len(result.root.children) == 2
    assert result.root.children[0].row["nombre"] == "Ana"
    assert result.root.children[0].row["monto"] == 100
    assert result.root.children[1].row["monto"] == 50


def test_read_csv_filelike():
    src = io.StringIO("nombre,monto\nAna,100\n")

    result = Report.read(src, format="csv").detail("nombre", "monto").run()

    assert result.columns == ["nombre", "monto"]
    assert result.root.children[0].row == {"nombre": "Ana", "monto": 100}


# --- TSV ---
def test_read_tsv():
    src = io.StringIO("a\tb\n1\t2\n")

    rows = read_rows(src, format="tsv")

    assert rows == [{"a": 1, "b": 2}]


# --- JSON / JSONL ---
def test_read_json():
    src = '[{"a": 1, "b": 2}, {"a": 3, "b": 4}]'

    rows = read_rows(src, format="json")

    assert rows == [{"a": 1, "b": 2}, {"a": 3, "b": 4}]


def test_read_jsonl():
    src = '{"a": 1}\n{"a": 2}\n'

    rows = read_rows(src, format="jsonl")

    assert rows == [{"a": 1}, {"a": 2}]


# --- tuplas ---
def test_read_tuples_requires_columns():
    with pytest.raises(ValueError):
        read_rows([("x", 1)], format="tuples")


def test_read_tuples():
    rows = read_rows([("Ana", 100), ("Bob", 50)], format="tuples", columns=["n", "m"])

    assert rows == [{"n": "Ana", "m": 100}, {"n": "Bob", "m": 50}]


# --- auto-detección en CSV ---
def test_auto_detection():
    src = io.StringIO("entero,decimal,booleano,vacio,texto\n100,100.5,true,,N/A\n")

    rows = read_rows(src, format="csv")

    assert rows == [
        {
            "entero": 100,
            "decimal": 100.5,
            "booleano": True,
            "vacio": None,
            "texto": "N/A",
        }
    ]
    assert isinstance(rows[0]["entero"], int)
    assert isinstance(rows[0]["decimal"], float)
    assert isinstance(rows[0]["booleano"], bool)
    assert rows[0]["vacio"] is None
    assert isinstance(rows[0]["texto"], str)


def test_coerce_false():
    src = io.StringIO("a,b\n100,true\n")

    rows = read_rows(src, format="csv", coerce=False)

    assert rows == [{"a": "100", "b": "true"}]
    assert all(isinstance(v, str) for r in rows for v in r.values())


# --- reader custom ---
class _MiReader:
    def read(self, source, **opts):
        return [{"x": 1}]


def test_custom_reader():
    Report.register_reader("mi", _MiReader())

    result = Report.read("ignorado", format="mi").detail("x").run()

    assert result.columns == ["x"]
    assert result.root.children[0].row["x"] == 1


# --- excel ---
def test_excel_reader(tmp_path):
    pytest.importorskip("openpyxl")
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.append(["a", "b"])
    ws.append([1, 2])
    path = tmp_path / "datos.xlsx"
    wb.save(path)

    result = Report.read(path).detail("a", "b").run()

    assert result.columns == ["a", "b"]
    assert result.root.children[0].row == {"a": 1, "b": 2}


def test_excel_missing_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "openpyxl", None)
    with pytest.raises(ImportError):
        read_rows("datos.xlsx", format="excel")


# --- compatibilidad con Report(rows=...) ---
def test_report_rows_unchanged():
    rows = [{"sku": "A", "cantidad": 2}, {"sku": "B", "cantidad": 1}]

    result = Report(rows).detail("sku", "cantidad").run()

    assert result.columns == ["sku", "cantidad"]
    assert len(result.root.children) == 2
    assert result.root.children[0].row["sku"] == "A"
