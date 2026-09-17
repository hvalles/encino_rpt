import pytest

from encino_rpt import Report
from encino_rpt.models import Format
from encino_rpt.renderers._format import format_value


def test_format_value_currency():
    fmt = Format(kind="currency", symbol="$", decimals=2, thousands=True, negative="paren")
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
    fmt = Format(kind="currency", symbol="$", decimals=None, thousands=True, negative="paren")
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
        c.value for row in ws.iter_rows() for c in row
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
        c.value for row in ws.iter_rows() for c in row
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

    restored = ReportResult.model_validate(data)
    assert restored.root.totals[0].value == 2


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
    # regresión documenta bug conocido — ver CONCERNS.md §Performance
    # (serialización JSON de árboles profundos)
    n = 1100
    path = ".".join(str(i) for i in range(n))
    rows = [{"cuenta": path, "monto": 7}]
    rep = Report(rows)
    rep.group("cuentas", path="cuenta")
    rep.detail("cuenta", "monto")
    rep.group("global")
    result = rep.run()

    # pydantic-core lanza ValueError "Circular reference detected (depth exceeded)", no RecursionError
    with pytest.raises(ValueError):
        result.to_json()


def test_excel_styles_footer_dead_params():
    pytest.importorskip("openpyxl")
    # regresión documenta bug conocido — ver CONCERNS.md §Tech Debt
    # (styles/footer muertos)
    rows = [{"sku": "A", "monto": 100}]
    rep = Report(rows)
    rep.detail("sku", "monto")
    rep.group("global")
    rep.section("global").footer("Total", column_position="monto")
    rep.section("global").total("sum", "monto")
    result = rep.run()

    # styles y column_position son no-op (sin crash); el footer se renderiza como fila completa
    ws = result.to_excel(styles={"bold": True})
    assert "Total" in [c.value for row in ws.iter_rows() for c in row]

