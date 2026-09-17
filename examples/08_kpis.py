"""08 — KPIs (tarjetas de resumen)."""

from _common import DATA, save

from encino_rpt import Report

CURRENCY = {"kind": "currency", "symbol": "$", "decimals": 2, "thousands": True}


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="KPIs de ventas")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)")

    rep.kpi("Transacciones", operator="count")
    rep.kpi("Importe total", operator="sum", column="importe", format=CURRENCY)
    rep.kpi("Ticket promedio", operator="avg", column="importe", format=CURRENCY)
    rep.kpi("SKUs distintos", operator="count_distinct", column="sku")

    rep.detail("fecha", "agente", "sku", "importe")

    save(rep.run(), "08_kpis")


if __name__ == "__main__":
    main()
