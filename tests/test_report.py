import pytest

from encino_rpt import Chart, Detail, Group, Pivot, Report, ReportResult
from encino_rpt.expressions import ExpressionError, evaluate


# --- evaluador de expresiones ---
def test_expression_arithmetic():
    row = {"cantidad": 3, "precio": 10}
    assert evaluate("cantidad * precio", row) == 30
    assert evaluate("cantidad + 1", row) == 4
    assert evaluate("2 ** 3", row) == 8
    assert evaluate("10 % 3", row) == 1
    assert evaluate("-cantidad", row) == -3


def test_expression_functions():
    row = {"nombre": "Ana", "pedido_id": 4}
    assert evaluate("IF(pedido_id % 2 == 0)", row) == 1
    assert evaluate("upper(nombre)", row) == "ANA"
    assert evaluate("lower(nombre)", row) == "ana"
    assert evaluate("concat(nombre, '-', 'X')", row) == "Ana-X"
    assert evaluate("round(3.14159, 2)", row) == 3.14
    assert evaluate("abs(-5)", row) == 5
    assert evaluate("AND(1, 0)", row) == 0
    assert evaluate("OR(1, 0)", row) == 1
    assert evaluate("NOT(0)", row) == 1
    assert evaluate("IN(2, 1, 2, 3)", row) == 1
    assert evaluate("BETWEEN(5, 1, 10)", row) == 1


def test_expression_rejects_unsafe():
    with pytest.raises(ExpressionError):
        evaluate("__import__('os')", {})
    with pytest.raises(ExpressionError):
        evaluate("(lambda: 1)()", {})
    with pytest.raises(ExpressionError):
        evaluate("x.__class__", {"x": 1})


# --- builder / agregación ---
def test_basic_report_and_hidden_fields():
    rows = [
        {"sku": "A", "cantidad": 2, "precio": 10.0},
        {"sku": "B", "cantidad": 1, "precio": 5.0},
    ]
    rep = Report(rows)
    rep.add_field("total", "cantidad * precio", after="precio")
    rep.add_field("es_doble", "IF(cantidad > 1)")  # oculto
    rep.detail("sku", "cantidad", "precio", "total")
    result = rep.run()

    assert result.columns == ["sku", "cantidad", "precio", "total"]
    assert result.root.name == "global"
    assert len(result.root.children) == 2
    assert result.root.children[0].row["total"] == 20.0
    assert result.root.children[1].row["total"] == 5.0
    # oculto: no aparece en las columnas ni en el detalle
    assert "es_doble" not in result.columns
    assert "es_doble" not in result.root.children[0].row


def test_group_and_totals():
    rows = [
        {"agente": "Ana", "monto": 100},
        {"agente": "Ana", "monto": 50},
        {"agente": "Bob", "monto": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente {{agente}}")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    result = rep.run()

    root = result.root
    assert root.name == "global"
    assert root.totals[0].value == 350
    assert len(root.children) == 2
    ana, bob = root.children
    assert ana.key == {"agente": "Ana"}
    assert ana.totals[0].value == 150
    assert ana.header == "Agente Ana"
    assert bob.key == {"agente": "Bob"}


def test_multi_column_group():
    rows = [
        {"tenant": 1, "code": "a", "total": 10},
        {"tenant": 1, "code": "b", "total": 20},
        {"tenant": 2, "code": "a", "total": 30},
    ]
    rep = Report(rows)
    rep.group("por_tenant_code", columns=["tenant", "code"])
    rep.section("por_tenant_code").total("sum", "total")
    rep.group("global")
    result = rep.run()

    assert [c.key for c in result.root.children] == [
        {"tenant": 1, "code": "a"},
        {"tenant": 1, "code": "b"},
        {"tenant": 2, "code": "a"},
    ]
    assert [c.totals[0].value for c in result.root.children] == [10, 20, 30]


def test_conditional_total():
    rows = [
        {"pedido_id": 1, "total": 100},
        {"pedido_id": 2, "total": 200},
        {"pedido_id": 3, "total": 300},
    ]
    rep = Report(rows)
    rep.add_field("es_par", "IF(pedido_id % 2 == 0)")
    rep.group("global")
    rep.section("global").total("sum", expression="es_par * total")
    result = rep.run()
    assert result.root.totals[0].value == 200


def test_phase_b_percentage():
    rows = [
        {"agente": "Ana", "total": 100},
        {"agente": "Bob", "total": 300},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total")
    rep.group("global")
    rep.section("global").total("sum", "total", name="total_gral")
    rep.section("por_agente").total("sum", expression="total / TOTAL('global.total_gral') * 100")
    result = rep.run()

    ana, bob = result.root.children
    assert ana.totals[1].value == 25.0
    assert bob.totals[1].value == 75.0
    assert result.root.totals[0].value == 400


def test_cumulative():
    rows = [
        {"debe": 100, "haber": 0},
        {"debe": 50, "haber": 20},
        {"debe": 0, "haber": 10},
    ]
    rep = Report(rows)
    rep.add_field("saldo", "debe - haber", cumulative="sum", start=0, after="haber")
    rep.detail("debe", "haber", "saldo")
    result = rep.run()
    assert [c.row["saldo"] for c in result.root.children] == [100, 130, 120]


def test_chart_and_pivot():
    rows = [
        {"agente": "Ana", "mes": "ene", "total": 100},
        {"agente": "Ana", "mes": "feb", "total": 50},
        {"agente": "Bob", "mes": "ene", "total": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total")
    rep.group("global")
    rep.section("global").chart("pie", operator="sum", column="total", label_field="agente")
    rep.section("global").pivot("agente", "mes", operator="sum", value_column="total")
    result = rep.run()

    # extras: [chart, pivot] al final de children
    chart, pivot = result.root.children[-2], result.root.children[-1]
    assert isinstance(chart, Chart)
    assert chart.labels == ["Ana", "Bob"]
    assert chart.series[0].values == [150, 200]

    assert isinstance(pivot, Pivot)
    assert pivot.rows == ["Ana", "Bob"]
    assert pivot.columns == ["ene", "feb"]
    assert pivot.cells == [[100, 50], [200, None]]
    assert pivot.row_totals == [150, 200]
    assert pivot.column_totals == [300, 50]


def test_order_top_suppress():
    rows = [
        {"agente": "Ana", "total": 100},
        {"agente": "Bob", "total": 300},
        {"agente": "Cid", "total": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total", name="total_agt")
    rep.group("global")
    rep.section("global").order_by(total="total_agt", direction="desc").top(2)
    result = rep.run()

    assert [c.key["agente"] for c in result.root.children] == ["Bob", "Cid"]


def test_order_by_expression_with_custom_function():
    rows = [
        {"agente": "Ana", "total": 100},
        {"agente": "Bob", "total": 300},
        {"agente": "Cid", "total": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total", name="total_agt")
    rep.group("global")
    rep.add_function("doblado", lambda v: v * 2)
    rep.section("global").order_by(expression="doblado(total)", direction="desc")
    result = rep.run()

    assert [c.key["agente"] for c in result.root.children] == ["Bob", "Cid", "Ana"]


def test_order_by_missing_total_raises():
    rows = [
        {"agente": "Ana", "total": 100},
        {"agente": "Bob", "total": 300},
        {"agente": "Cid", "total": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total", name="total_agt")
    rep.group("global")
    rep.section("global").order_by(total="total_inexistente")

    with pytest.raises(ValueError, match="total de orden inexistente: 'total_inexistente'"):
        rep.run()


def test_order_by_missing_column_raises():
    rows = [
        {"agente": "Ana", "total": 100},
        {"agente": "Bob", "total": 300},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total", name="total_agt")
    rep.group("global")
    rep.section("global").order_by(column="columna_inexistente")

    with pytest.raises(ValueError, match="columna de orden inexistente: 'columna_inexistente'"):
        rep.run()


def test_order_by_total_on_detail_names_child():
    rows = [{"agente": "Ana", "total": 100}]
    rep = Report(rows)
    rep.detail("agente", "total")
    rep.group("global")
    rep.section("global").order_by(total="total_inexistente")

    with pytest.raises(ValueError, match="total de orden inexistente") as exc:
        rep.run()
    assert "(hijo 'Detail')" in str(exc.value)


def test_link_and_image():
    rows = [{"id": 1, "sku": "A1"}]
    rep = Report(rows)
    rep.link("ver", "report", href="/pedido/{{id}}", label="Ver", after="id")
    rep.image("foto", src="/media/{{sku}}.png", after="sku")
    rep.detail("id", "sku")
    result = rep.run()

    assert result.columns == ["id", "ver", "sku", "foto"]
    row = result.root.children[0].row
    assert row["ver"].href == "/pedido/1"
    assert row["ver"].target == "report"
    assert row["foto"].src == "/media/A1.png"


def test_format_and_styles():
    rows = [{"total": 1234.5}]
    rep = Report(rows)
    rep.set_format("total", kind="currency", symbol="$", decimals=2, thousands=True)
    rep.add_style("total", when="lt", value=0, color="red")
    result = rep.run()
    assert result.formats["total"].symbol == "$"
    assert result.formats["total"].thousands is True
    assert result.styles[0].when == "lt"
    assert result.styles[0].style == {"color": "red"}


def test_kpi():
    rows = [{"total": 100}, {"total": 200}]
    rep = Report(rows)
    rep.kpi("Ingresos", operator="sum", column="total")
    rep.kpi("Ticket", operator="avg", column="total")
    result = rep.run()
    assert result.kpis[0].value == 300
    assert result.kpis[1].value == 150


def test_report_result_roundtrip():
    rows = [{"sku": "A", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    result = rep.run()
    data = result.model_dump()
    assert data["root"]["type"] == "group"
    restored = ReportResult.model_validate(data)
    assert restored.columns == ["sku", "cantidad"]


def test_path_group():
    rows = [
        {"cuenta": "1", "monto": 10},
        {"cuenta": "1.1", "monto": 20},
        {"cuenta": "1.1.1", "monto": 30},
        {"cuenta": "2", "monto": 40},
    ]
    rep = Report(rows)
    rep.group("cuentas", path="cuenta")
    rep.section("cuentas").total("sum", "monto")
    rep.detail("cuenta", "monto")
    rep.group("global")
    result = rep.run()

    root = result.root
    assert [c.key for c in root.children] == [{"cuenta": "1"}, {"cuenta": "2"}]
    uno = root.children[0]
    assert uno.totals[0].value == 60  # 10 + 20 + 30
    # "1" tiene un detalle (cuenta "1") y un subgrupo "1.1"
    assert isinstance(uno.children[0], Detail)
    assert uno.children[0].row["monto"] == 10
    assert uno.children[1].key == {"cuenta": "1.1"}
    assert uno.children[1].totals[0].value == 50


# --- idempotencia ---
def test_run_is_idempotent():
    rows = [{"agente": "Ana", "monto": 100}, {"agente": "Bob", "monto": 200}]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    first = rep.run()
    second = rep.run()
    assert first.model_dump() == second.model_dump()
    assert len(second.root.children) == 2


def test_duplicate_group_name_raises():
    rows = [{"a": 1}]
    rep = Report(rows)
    rep.group("g", columns="a")
    with pytest.raises(ValueError, match="corte ya declarado"):
        rep.group("g", columns="a")


def test_parent_not_declared_raises():
    rows = [{"a": 1}]
    rep = Report(rows)
    rep.group("hijo", columns="a", parent="noexiste")
    with pytest.raises(ValueError, match="padre no declarado: 'noexiste'"):
        rep.run()


# --- errores con contexto ---
def test_aggregation_error_context():
    from encino_rpt.aggregation import AggregationError

    rows = [{"monto": 0}]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").total("sum", expression="1 / monto")
    with pytest.raises(AggregationError, match="grupo 'global'"):
        rep.run()


def test_custom_aggregate_missing():
    from encino_rpt.aggregation import AggregationError

    rows = [{"monto": 100}]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").total("custom:noexiste", "monto")
    with pytest.raises(AggregationError, match="agregado custom no registrado"):
        rep.run()


def test_unknown_source_raises():
    rows = [{"monto": 100}]
    rep = Report(rows)
    rep.group("global", source="noexiste")
    with pytest.raises(ValueError, match="source no declarado: 'noexiste'"):
        rep.run()


# --- rendimiento ---
def test_pivot_single_pass():
    from encino_rpt._specs import PivotSpec
    from encino_rpt.pivot import build_pivot

    rows = [
        {"fila": "A", "col": "x", "v": 1},
        {"fila": "A", "col": "y", "v": 2},
        {"fila": "B", "col": "x", "v": 3},
    ]
    processed = []

    def value_fn(group):
        processed.append(len(group))
        return sum(r["v"] for r in group)

    spec = PivotSpec(row_column="fila", column_column="col", value_column="v")
    pivot = build_pivot(spec, rows, value_fn)

    assert pivot.row_totals == [3, 3]
    assert pivot.column_totals == [4, 2]
    # una sola pasada: celdas + filas + columnas, sin re-escaneo O(filas x uniques)
    assert len(processed) == 3 + 2 + 2
    assert sum(processed) == len(rows) * 3


def test_path_group_deep_no_recursion():
    n = 1100
    path = ".".join(str(i) for i in range(n))
    rows = [{"cuenta": path, "monto": 7}]
    rep = Report(rows)
    rep.group("cuentas", path="cuenta")
    rep.section("cuentas").total("sum", "monto")
    rep.detail("cuenta", "monto")
    rep.group("global")
    result = rep.run()

    node = result.root
    depth = 0
    while isinstance(node, Group) and node.children and isinstance(node.children[0], Group):
        node = node.children[0]
        depth += 1
    assert isinstance(node.children[0], Detail)
    assert node.children[0].row["monto"] == 7
    assert depth == n


# --- regresiones TEST-01 (multi-dataset y no-op) ---
def test_multi_dataset_source():
    primary = [{"agente": "Ana", "monto": 100}]
    rep = Report(primary)
    rep.add_dataset("presupuesto", [
        {"agente": "Bob", "monto": 10},
        {"agente": "Cid", "monto": 20},
    ])
    rep.group("por_agente", columns="agente", source="presupuesto")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    result = rep.run()

    assert [c.key["agente"] for c in result.root.children] == ["Bob", "Cid"]
    assert [c.totals[0].value for c in result.root.children] == [10, 20]


def test_suppress_zero_missing_column():
    # regresión documenta bug conocido — ver CONCERNS.md §Known Bugs (suppress_zero)
    rows = [
        {"agente": "Ana", "monto": 100},
        {"agente": "Bob", "monto": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").suppress_zero(column="columna_inexistente")
    result = rep.run()

    assert len(result.root.children) == 0


@pytest.mark.xfail(strict=True, reason="bug conocido — ver CONCERNS.md §Known Bugs (detail(source=...) ignorado)")
def test_detail_source_ignored():
    primary = [{"sku": "A", "monto": 100}]
    secondary = [{"sku": "B", "monto": 999}]
    rep = Report(primary)
    rep.add_dataset("presupuesto", secondary)
    rep.detail("sku", "monto", source="presupuesto")
    result = rep.run()

    assert result.root.children[0].row["sku"] == "B"


def test_count_expression_semantics():
    # regresión documenta bug conocido — ver CONCERNS.md §Known Bugs (count truthy vs rows)
    rows = [{"monto": 10}, {"monto": -5}, {"monto": 0}]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").total("count", expression="monto > 0")
    result = rep.run()

    assert result.root.totals[0].value == 1

