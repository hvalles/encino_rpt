"""04 — Totales condicionales y porcentaje sobre el total general (TOTAL)."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(
        DATA / "ventas.csv", title="Importe, ventas grandes y % del total"
    )
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("sku", "producto", "importe")

    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "importe", label="Total agente")
    # Total condicional: solo los renglones cuyo importe supera 500.
    rep.section("por_agente").total(
        "sum", expression="importe * (importe > 500)", label="Grandes (>500)"
    )
    # Fase B: % de cada agente sobre el total general (referencia cruzada).
    rep.section("por_agente").total(
        "sum",
        expression="importe / TOTAL('global.total_gral') * 100",
        label="% del total",
        format={"kind": "percent", "decimals": 1},
    )

    rep.group("global")
    rep.section("global").total("sum", "importe", name="total_gral")

    save(rep.run(), "04_totales_condicionales")


if __name__ == "__main__":
    main()
