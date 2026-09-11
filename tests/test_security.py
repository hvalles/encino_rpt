import pytest

from encino_rpt import Report
from encino_rpt.expressions import ExpressionError, evaluate
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
