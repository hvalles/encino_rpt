import pytest

from encino_rpt import Report
from encino_rpt.models import Format
from encino_rpt.renderers._format import format_value


def test_format_value_currency():
    fmt = Format(
        kind="currency", symbol="$", decimals=2, thousands=True, negative="paren"
    )
    assert format_value(1234.5, fmt) == "$1,234.50"
    assert format_value(-1234.5, fmt) == "($1,234.50)"


def test_format_value_percent():
    fmt = Format(kind="percent", decimals=1, percent_scale=True)
    assert format_value(0.256, fmt) == "25.6%"


def test_format_value_number():
    assert format_value(1.234, Format(decimals=2)) == "1.23"
    assert format_value(None, Format()) == ""
    assert format_value(5, None) == "5"


def test_format_value_precision_no_sci():
    assert format_value(1234567.89, Format()) == "1234567.89"


def test_format_value_precision_thousands():
    assert format_value(1234567.89, Format(thousands=True)) == "1,234,567.89"


def test_format_value_precision_percent_scale():
    assert format_value(0.07, Format(kind="percent", percent_scale=True)) == "7%"
    assert format_value(0.29, Format(kind="percent", percent_scale=True)) == "29%"
    assert format_value(0.256, Format(kind="percent", percent_scale=True)) == "25.6%"


def test_format_value_precision_sci_extremes():
    assert format_value(1e16, Format()) == "1e+16"
    assert format_value(0.00001, Format()) == "1e-05"


def test_format_value_precision_whole_float():
    assert format_value(2.0, Format()) == "2.0"


def test_format_value_precision_currency():
    fmt = Format(
        kind="currency", symbol="$", decimals=None, thousands=True, negative="paren"
    )
    assert format_value(-1234567.89, fmt) == "($1,234,567.89)"


def test_text_renderer():
    rows = [{"agente": "Ana", "monto": 100}, {"agente": "Bob", "monto": 200}]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente {{agente}}")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    rep.detail("agente", "monto")
    result = rep.run()

    text = result.to_text()
    assert "Agente Ana" in text
    assert "Agente Bob" in text
    assert "sum: 100" in text
    assert "sum: 300" in text


def test_csv_renderer():
    rows = [{"sku": "A", "cantidad": 2}, {"sku": "B", "cantidad": 1}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    result = rep.run()
    csv_out = result.to_csv()
    assert "A,2" in csv_out
    assert "B,1" in csv_out


def test_html_renderer_and_styles():
    rows = [{"total": -5}, {"total": 10}]
    rep = Report(rows)
    rep.detail("total")
    rep.add_style("total", when="lt", value=0, color="red")
    result = rep.run()

    html_out = result.render_html()
    assert "<table>" in html_out
    assert "<th>total</th>" in html_out
    assert "color:red" in html_out


# --- HTML modo clases (TMPL-01) ---
def test_html_css_mode_no_inline_style():
    rows = [{"total": -5}, {"total": 10}]
    rep = Report(rows)
    rep.detail("total")
    rep.add_style("total", when="lt", value=0, color="red")
    result = rep.run()

    html_out = result.render_html(css=True)
    assert "rpt-cond-0" in html_out
    assert "<style>" in html_out
    assert "color:red" in html_out
    # la celda condicional usa clase, no style inline
    assert '<td class="rpt-cond-0">' in html_out
    assert '<td style="' not in html_out


def test_html_css_mode_default_unchanged():
    rows = [{"total": -5}]
    rep = Report(rows)
    rep.detail("total")
    rep.add_style("total", when="lt", value=0, color="red")
    result = rep.run()

    html_out = result.render_html()
    assert 'style="color:red"' in html_out
    assert "<style>" not in html_out


# --- HTML template de documento (TMPL-02) ---
def test_html_template_document():
    rows = [{"total": 10}]
    rep = Report(rows, title="Mi Reporte")
    rep.detail("total")
    result = rep.run()

    html_out = result.render_html(template=True)
    assert html_out.startswith("<!DOCTYPE html>")
    assert "<head>" in html_out
    assert '<body class="report">' in html_out
    assert "<title>Mi Reporte</title>" in html_out
    # el fragmento por defecto no envuelve
    assert not result.render_html().startswith("<!DOCTYPE html>")


def test_html_template_with_css_style_in_head():
    rows = [{"total": -5}]
    rep = Report(rows, title="T")
    rep.detail("total")
    rep.add_style("total", when="lt", value=0, color="red")
    result = rep.run()

    html_out = result.render_html(template=True, css=True)
    assert "<style>.rpt-cond-0{color:red}</style>" in html_out
    assert "<head>" in html_out
    assert html_out.index("<style>") < html_out.index("</head>")


# --- Markdown (TMPL-03) ---
def test_markdown_renderer():
    rows = [{"sku": "A", "cantidad": 2}, {"sku": "B", "cantidad": 1}]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").header("Resumen")
    rep.section("global").total("sum", "cantidad", label="total")
    rep.detail("sku", "cantidad")
    result = rep.run()

    md = result.to_markdown()
    assert "## Resumen" in md
    assert "**total:** 3" in md
    assert "| sku | cantidad |" in md
    assert "|---|---|" in md


def test_markdown_link_image():
    rows = [{"id": 1, "sku": "A1"}]
    rep = Report(rows)
    rep.link("ver", "report", href="/pedido/{{id}}", label="Ver", after="id")
    rep.image("foto", src="/media/{{sku}}.png", alt="Foto", after="sku")
    rep.detail("id", "sku")
    result = rep.run()

    md = result.to_markdown()
    assert "[Ver](/pedido/1)" in md
    assert "![Foto](/media/A1.png)" in md


def test_markdown_escapes_pipe():
    rows = [{"nombre": "a|b", "monto": 1}]
    rep = Report(rows)
    rep.detail("nombre", "monto")
    result = rep.run()

    md = result.to_markdown()
    assert "a\\|b" in md


def test_markdown_escapes_link_parens():
    rows = [{"id": 1}]
    rep = Report(rows)
    rep.link("ver", "report", href="/x?a=b)c", label="a|b", after="id")
    rep.detail("id")
    result = rep.run()

    md = result.to_markdown()
    assert "a\\|b" in md
    assert "/x?a=b\\)c" in md


def test_excel_renderer():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "A", "cantidad": 2}, {"sku": "B", "cantidad": 1}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    rep.group("global")
    rep.section("global").total("sum", "cantidad")
    result = rep.run()

    ws = result.to_excel()
    assert ws["A1"].value == "sku"
    assert ws["B1"].value == "cantidad"
    assert ws["A2"].value == "A"
    assert ws["B2"].value == 2
    assert ws["A4"].value == "sum"


def test_excel_formulas():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "A", "cantidad": 2}, {"sku": "B", "cantidad": 1}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    rep.group("global")
    rep.section("global").total("sum", "cantidad")
    result = rep.run()

    ws = result.to_excel(formulas=True)
    formula_cells = [
        c.value
        for row in ws.iter_rows()
        for c in row
        if isinstance(c.value, str) and c.value.startswith("=")
    ]
    assert any("SUM" in f for f in formula_cells)


def test_excel_formulas_no_double_count():
    pytest.importorskip("openpyxl")
    rows = [
        {"agente": "Ana", "monto": 100},
        {"agente": "Ana", "monto": 50},
        {"agente": "Bob", "monto": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    rep.detail("agente", "monto")
    result = rep.run()

    ws = result.to_excel(formulas=True)
    formulas = {
        c.value
        for row in ws.iter_rows()
        for c in row
        if isinstance(c.value, str) and c.value.startswith("=")
    }
    # subtotales y total global referencian SOLO filas de detalle (sin doble conteo)
    assert "=SUM(B2:B3)" in formulas
    assert "=SUM(B5)" in formulas
    assert "=SUM(B2:B3,B5)" in formulas
    # el total global NO abarca las filas de subtotal (B4, B6)
    assert "=SUM(B2:B6)" not in formulas


def test_excel_number_format():
    pytest.importorskip("openpyxl")
    rows = [{"total": 1234.5}]
    rep = Report(rows)
    rep.detail("total")
    rep.set_format("total", kind="currency", symbol="$", decimals=2, thousands=True)
    result = rep.run()
    ws = result.to_excel()
    assert ws["A2"].value == 1234.5
    assert "$" in ws["A2"].number_format


def test_pdf_renderer():
    pytest.importorskip("reportlab")
    rows = [{"sku": "A", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    result = rep.run()
    pdf = result.to_pdf()
    assert pdf[:5] == b"%PDF-"


# --- Link/Image ---
def test_link_image_html():
    rows = [{"id": 1, "sku": "A1"}]
    rep = Report(rows)
    rep.link("ver", "report", href="/pedido/{{id}}", label="Ver", after="id")
    rep.image("foto", src="/media/{{sku}}.png", alt="Foto", after="sku")
    rep.detail("id", "sku")
    result = rep.run()
    html_out = result.render_html()
    assert '<a href="/pedido/1">Ver</a>' in html_out
    assert '<img src="/media/A1.png" alt="Foto"/>' in html_out
    assert "type='link'" not in html_out


def test_link_excel():
    pytest.importorskip("openpyxl")
    rows = [{"id": 1}]
    rep = Report(rows)
    rep.link("ver", "external", href="/pedido/{{id}}", label="Ver", after="id")
    rep.detail("id")
    result = rep.run()
    ws = result.to_excel()
    assert ws["B1"].value == "ver"
    cell = ws["B2"]
    assert cell.value == "Ver"
    assert cell.hyperlink.target == "/pedido/1"


def test_link_image_csv():
    rows = [{"id": 1, "sku": "A1"}]
    rep = Report(rows)
    rep.link("ver", "report", href="/pedido/{{id}}", label="Ver", after="id")
    rep.image("foto", src="/media/{{sku}}.png", after="sku")
    rep.detail("id", "sku")
    result = rep.run()
    csv_out = result.to_csv()
    assert "Ver" in csv_out
    assert "/media/A1.png" in csv_out


def test_link_image_text():
    rows = [{"id": 1, "sku": "A1"}]
    rep = Report(rows)
    rep.link("ver", "report", href="/pedido/{{id}}", label="Ver", after="id")
    rep.image("foto", src="/media/{{sku}}.png", after="sku")
    rep.detail("id", "sku")
    result = rep.run()
    text = result.to_text()
    assert "Ver -> /pedido/1" in text
    assert "/media/A1.png" in text


# --- layout (FEAT-02) ---
def test_excel_total_column_position():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "A", "monto": 100, "nota": "x"}]
    rep = Report(rows)
    rep.detail("sku", "monto", "nota")
    rep.group("global")
    rep.section("global").total("sum", "monto", column_position="nota")
    result = rep.run()
    ws = result.to_excel()
    assert ws["A3"].value == "sum"
    assert ws["B3"].value is None
    assert ws["C3"].value == 100


def test_html_page_break_class():
    rows = [{"agente": "Ana", "monto": 100}]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente {{agente}}").page_break()
    rep.group("global")
    result = rep.run()
    html_out = result.render_html()
    assert "page-break" in html_out


def test_html_repeat_header():
    rows = [{"agente": "Ana", "monto": 100}, {"agente": "Bob", "monto": 200}]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente {{agente}}")
    rep.detail("agente", "monto")
    rep.group("global")
    result = rep.run()
    html_out = result.render_html(repeat_header=True)
    assert html_out.count('<tr class="header">') == 2


def test_html_default_collapsed():
    rows = [{"agente": "Ana", "monto": 100}]
    rep = Report(rows)
    rep.group("por_agente", columns="agente", default_collapsed=True)
    rep.section("por_agente").header("Agente {{agente}}")
    rep.group("global")
    result = rep.run()
    html_out = result.render_html()
    assert "<details>" in html_out
    assert "<summary>Agente Ana</summary>" in html_out


# --- JSON versionado (JSON-01) ---
def test_json_renderer_roundtrip():
    import json

    from encino_rpt import ReportResult

    rows = [{"sku": "A", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    rep.group("global")
    rep.section("global").total("sum", "cantidad")
    result = rep.run()

    data = json.loads(result.to_json())
    assert data["schema_version"] == "1.0"
    assert data["root"]["type"] == "group"

    restored = ReportResult.from_dict(data)
    assert restored.root.totals[0].value == 2


def test_roundtrip_full_tree():
    # round-trip del reconstructor `from_dict` sobre todos los tipos de nodo.
    from encino_rpt import ReportResult

    rows = [
        {"agente": "Ana", "sku": "A", "monto": 100},
        {"agente": "Ana", "sku": "B", "monto": 50},
        {"agente": "Bob", "sku": "A", "monto": 200},
    ]
    rep = Report(rows)
    rep.link("ver", "report", href="/p/{{sku}}", label="Ver", after="sku")
    rep.detail("sku", "agente", "monto")
    rep.set_format("monto", kind="currency", symbol="$", decimals=2)
    rep.add_style("monto", when="lt", value=100, color="red")
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "monto")
    rep.section("por_agente").chart(
        "pie", operator="sum", column="monto", label_field="sku"
    )
    rep.section("por_agente").pivot(
        "sku", "agente", operator="sum", value_column="monto"
    )
    rep.group("global")
    rep.section("global").total("sum", "monto")
    result = rep.run()

    data = result.to_dict()
    restored = ReportResult.from_dict(data)
    assert restored.to_dict() == data


def test_deep_path_renders_iteratively():
    n = 1100
    path = ".".join(str(i) for i in range(n))
    rows = [{"cuenta": path, "monto": 7}]
    rep = Report(rows)
    rep.group("cuentas", path="cuenta")
    rep.detail("cuenta", "monto")
    rep.group("global")
    result = rep.run()

    text = result.to_text()
    assert "monto=7" in text
    html_out = result.render_html()
    assert "<table>" in html_out


# --- regresiones TEST-01 (renderers) ---
def test_deep_tree_to_json():
    # CORR-14: jerarquía demasiado profunda -> ValueError claro, no RecursionError.
    n = 1100
    path = ".".join(str(i) for i in range(n))
    rows = [{"cuenta": path, "monto": 7}]
    rep = Report(rows)
    rep.group("cuentas", path="cuenta")
    rep.detail("cuenta", "monto")
    rep.group("global")
    result = rep.run()

    with pytest.raises(ValueError, match="demasiado profunda"):
        result.to_json()


def test_to_json_non_serializable_not_masked():
    # un valor no serializable lanza TypeError (no se enmascara como "profundo").
    rows = [{"sku": object(), "monto": 1}]
    rep = Report(rows)
    rep.detail("sku", "monto")
    result = rep.run()

    with pytest.raises(TypeError):
        result.to_json()


def test_excel_footer_renders_full_row():
    pytest.importorskip("openpyxl")
    # footer se renderiza como fila completa (los params muertos styles/footer
    # column_position fueron eliminados — ver CONCERNS.md §Tech Debt resuelto).
    rows = [{"sku": "A", "monto": 100}]
    rep = Report(rows)
    rep.detail("sku", "monto")
    rep.group("global")
    rep.section("global").footer("Total")
    rep.section("global").total("sum", "monto")
    result = rep.run()

    ws = result.to_excel()
    assert "Total" in [c.value for row in ws.iter_rows() for c in row]


def _streaming_report():
    rows = [{"sku": "A", "cantidad": 2}, {"sku": "B", "cantidad": 1}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    rep.group("global")
    rep.section("global").total("sum", "cantidad")
    return rep.run()


def test_iter_csv_matches_render():
    result = _streaming_report()
    assert list(result.iter_csv()) == result.to_csv().splitlines()


def test_to_csv_file_writes():
    import io

    result = _streaming_report()
    buf = io.StringIO()
    assert result.to_csv(file=buf) is None
    assert buf.getvalue() == result.to_csv()


def test_iter_text_matches_render():
    result = _streaming_report()
    assert list(result.iter_text()) == result.to_text().splitlines()


def test_iter_html_matches_render():
    result = _streaming_report()
    assert "".join(result.iter_html()) == result.render_html()


def test_iter_markdown_matches_render():
    result = _streaming_report()
    assert "\n".join(result.iter_markdown()) == result.to_markdown()


def test_to_pdf_file_writes():
    pytest.importorskip("reportlab")
    import io

    result = _streaming_report()
    buf = io.BytesIO()
    assert result.to_pdf(file=buf) is None
    assert buf.getvalue().startswith(b"%PDF")


def test_from_dict_missing_keys_use_defaults():
    from encino_rpt import ReportResult

    result = _streaming_report()
    data = result.to_dict()
    partial = {"root": data["root"]}
    restored = ReportResult.from_dict(partial)
    assert restored.columns == []
    assert restored.formats == {}
    assert restored.styles == []
    assert restored.kpis == []
    assert restored.meta.title is None


def test_set_format_invalid_kind_raises():
    rep = Report([{"a": 1}])
    with pytest.raises(ValueError, match="kind"):
        rep.set_format("a", kind="bogus")


def test_add_style_invalid_when_raises():
    rep = Report([{"a": 1}])
    with pytest.raises(ValueError, match="when"):
        rep.add_style("a", when="bogus", color="red")


# --- PRD (production readiness) ---
def _chart_pivot_report():
    rows = [
        {"agente": "Ana", "sku": "A", "monto": 100},
        {"agente": "Ana", "sku": "B", "monto": 50},
        {"agente": "Bob", "sku": "A", "monto": 200},
    ]
    rep = Report(rows)
    rep.detail("sku", "agente", "monto")
    rep.group("por_agente", columns="agente")
    sec = rep.section("por_agente")
    sec.total("sum", "monto")
    sec.chart("pie", title="Ventas", operator="sum", column="monto", label_field="sku")
    sec.pivot("sku", "agente", operator="sum", value_column="monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    return rep.run()


def test_chart_pivot_render_html():
    html = _chart_pivot_report().render_html()
    assert "Ventas" in html
    assert 'class="pivot"' in html


def test_chart_pivot_render_csv():
    out = _chart_pivot_report().to_csv()
    assert "chart:pie" in out


def test_chart_pivot_render_text():
    out = _chart_pivot_report().to_text()
    assert "[chart:pie]" in out
    assert "[pivot]" in out


def test_chart_pivot_render_markdown():
    out = _chart_pivot_report().to_markdown()
    assert "Ventas" in out
    assert "(pie)" in out


def test_chart_pivot_render_excel():
    pytest.importorskip("openpyxl")
    ws = _chart_pivot_report().to_excel()
    vals = [c.value for row in ws.iter_rows() for c in row]
    assert "pie Ventas" in vals
    assert "pivot" in vals


def test_chart_pivot_render_pdf():
    pytest.importorskip("reportlab")
    data = _chart_pivot_report().to_pdf()
    assert data.startswith(b"%PDF")


def test_deep_tree_to_dict_raises_clear():
    from encino_rpt import ReportResult

    n = 1100
    path = ".".join(str(i) for i in range(n))
    rows = [{"cuenta": path, "monto": 7}]
    rep = Report(rows)
    rep.group("cuentas", path="cuenta")
    rep.detail("cuenta", "monto")
    rep.group("global")
    result = rep.run()
    with pytest.raises(ValueError, match="demasiado profunda"):
        result.to_dict()
    with pytest.raises(ValueError, match="demasiado profunda"):
        ReportResult.from_dict(result.to_dict() if False else _deep_dict(n))


def _deep_dict(n):
    node = {"type": "detail", "row": {"x": 1}}
    for _ in range(n):
        node = {"type": "group", "name": "g", "children": [node]}
    return {"root": node}


def test_from_dict_rejects_unknown_node():
    from encino_rpt import ReportResult

    with pytest.raises(ValueError, match="nodo hijo inválido"):
        ReportResult.from_dict(
            {"root": {"type": "group", "name": "g", "children": [42]}}
        )
    with pytest.raises(ValueError, match="tipo de nodo"):
        ReportResult.from_dict(
            {"root": {"type": "group", "name": "g", "children": [{"type": "bogus"}]}}
        )


def test_model_literal_validation():
    from encino_rpt.models import Chart, ConditionalRule, Format, Link

    with pytest.raises(ValueError, match="kind"):
        Format(kind="bogus")
    with pytest.raises(ValueError, match="when"):
        ConditionalRule(when="bogus")
    with pytest.raises(ValueError, match="kind de gráfico"):
        Chart(kind="bogus")
    with pytest.raises(ValueError, match="target"):
        Link(target="bogus", href="/x")


def test_serialization_decimal_datetime():
    from datetime import datetime, timezone
    from decimal import Decimal

    from encino_rpt import ReportResult

    rows = [
        {"monto": Decimal("100.50"), "fecha": datetime(2024, 1, 2, tzinfo=timezone.utc)}
    ]
    rep = Report(rows)
    rep.detail("monto", "fecha")
    result = rep.run()

    d = result.to_dict()
    row = d["root"]["children"][0]["row"]
    assert row["monto"] == "100.50"
    assert row["fecha"] == "2024-01-02T00:00:00+00:00"
    assert ReportResult.from_dict(d).to_dict() == d
