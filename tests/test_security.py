import pytest

from encino_rpt import Report
from encino_rpt.expressions import ExpressionError, evaluate
from encino_rpt.renderers._sanitize import is_dangerous, sanitize_csv
from encino_rpt.template import render


# --- P1: inyección de fórmulas ---
def test_csv_formula_injection():
    rows = [{"sku": "=1+1", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    result = rep.run()
    out = result.to_csv()
    assert "'=1+1,2" in out


def test_excel_formula_injection():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "=1+1"}]
    rep = Report(rows)
    rep.detail("sku")
    result = rep.run()
    ws = result.to_excel()
    cell = ws["A2"]
    assert cell.value == "=1+1"
    assert cell.data_type == "s"


# --- P5: inyección de fórmulas con espacio/BOM ---
def test_is_dangerous_leading_space_bom():
    assert is_dangerous(" =1+1") is True
    assert is_dangerous("\ufeff=1+1") is True
    assert is_dangerous("\x0c=1+1") is True
    assert is_dangerous("\ufeff\t=1+1") is True
    assert is_dangerous("normal") is False


def test_sanitize_csv_leading_space_bom():
    assert sanitize_csv(" =1+1") == "' =1+1"
    assert sanitize_csv("\ufeff@evil") == "'\ufeff@evil"


def test_excel_leading_space_bom():
    pytest.importorskip("openpyxl")
    rows = [{"sku": " =1+1", "cantidad": "\ufeff@evil"}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    result = rep.run()
    ws = result.to_excel()
    cell = ws["A2"]
    assert cell.value == " =1+1"
    assert cell.data_type == "s"
    cell2 = ws["B2"]
    assert cell2.value == "\ufeff@evil"
    assert cell2.data_type == "s"


# --- P2: DoS en el evaluador ---
def test_expression_pow_limit():
    with pytest.raises(ExpressionError):
        evaluate("9 ** 9 ** 9 ** 9 ** 9", {})
    with pytest.raises(ExpressionError):
        evaluate("2 ** 10000000000", {})


def test_expression_complexity_limit():
    expr = "+".join(["1"] * 2000)
    with pytest.raises(ExpressionError):
        evaluate(expr, {})


# --- P3: estilos HTML ---
def test_html_style_injection_mitigated():
    rows = [{"total": -5}]
    rep = Report(rows)
    rep.detail("total")
    rep.add_style("total", when="lt", value=0, color='red" onmouseover="x')
    rep.add_style("total", when="lt", value=0, **{"background;position": "fixed"})
    result = rep.run()
    html_out = result.render_html()
    assert '" onmouseover="' not in html_out
    assert "background;position" not in html_out


# --- P4: índice param.N ---
def test_template_param_validation():
    assert render("{{param.0}}", {}, params=["a", "b"]) == "a"
    with pytest.raises(IndexError):
        render("{{param.5}}", {}, params=[1, 2])
    with pytest.raises(ValueError):
        render("{{param.}}", {}, params=[1, 2])


def test_unknown_template_token_raises():
    with pytest.raises(KeyError, match="token no resuelto"):
        render("x={{totals.monto}}", {})


# --- P2b: DoS en el evaluador (exponentes float y errores aritméticos) ---
def test_expression_float_exponent_limit():
    with pytest.raises(ExpressionError):
        evaluate("2 ** 1e100", {})


def test_expression_arithmetic_errors():
    with pytest.raises(ExpressionError):
        evaluate("1 / 0", {})
    with pytest.raises(ExpressionError):
        evaluate("2.0 ** 5000", {})


# --- P3b: inyección CSS vía valores con ';' ---
def test_html_style_value_injection_mitigated():
    rows = [{"total": -5}]
    rep = Report(rows)
    rep.detail("total")
    rep.add_style("total", when="lt", value=0, background="red;position:fixed")
    result = rep.run()
    html_out = result.render_html()
    assert "position:fixed" not in html_out


# --- P3c: inyección CSS en modo clases (css=True) ---
def test_html_css_mode_injection_mitigated():
    rows = [{"total": -5}]
    rep = Report(rows)
    rep.detail("total")
    rep.add_style("total", when="lt", value=0, background="red;position:fixed")
    result = rep.run()
    html_out = result.render_html(css=True)
    assert "position:fixed" not in html_out


# --- P1b: sanitización de labels/headers en Excel ---
def test_excel_total_label_sanitized():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "A", "total": 100}]
    rep = Report(rows)
    rep.detail("sku", "total")
    rep.group("global")
    rep.section("global").total("sum", "total", label="=1+1")
    result = rep.run()
    ws = result.to_excel()
    for row in ws.iter_rows():
        for cell in row:
            if cell.value == "=1+1":
                assert cell.data_type == "s"
                return
    pytest.fail("no se encontró la celda de total")


def test_excel_header_sanitized():
    pytest.importorskip("openpyxl")
    rows = [{"=1+1": 1}]
    rep = Report(rows)
    rep.detail("=1+1")
    result = rep.run()
    ws = result.to_excel()
    assert ws["A1"].value == "=1+1"
    assert ws["A1"].data_type == "s"


# --- regresiones TEST-01 (seguridad) ---
def test_expression_null_byte():
    # PRD-01: el null byte debe lanzar ExpressionError de forma uniforme
    # (antes era ValueError crudo en 3.10 y ExpressionError en 3.11+).
    with pytest.raises(ExpressionError):
        evaluate("\x00", {})


def test_excel_formula_mode_no_user_injection():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "=1+1", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    rep.group("global")
    rep.section("global").total("sum", "cantidad")
    result = rep.run()

    ws = result.to_excel(formulas=True)
    # valor de usuario NUNCA es fórmula viva (saneado a texto)
    assert ws["A2"].value == "=1+1"
    assert ws["A2"].data_type == "s"
    # solo la fórmula SUM interna (generada por índices de fila) es fórmula viva
    assert [c.value for row in ws.iter_rows() for c in row if c.data_type == "f"] == [
        "=SUM(B2)"
    ]
