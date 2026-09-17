"""10 — Multi-dataset: comparar ventas contra presupuesto (source=)."""

import json

from _common import DATA, save

from encino_rpt import Report

CURRENCY = {"kind": "currency", "symbol": "$", "decimals": 2, "thousands": True}
IMPORTE = "cantidad * precio * (1 - descuento)"


def main() -> None:
    presupuesto = json.loads((DATA / "presupuesto.json").read_text(encoding="utf-8"))

    rep = Report.read(DATA / "ventas.csv", title="Ventas vs presupuesto")
    rep.add_dataset("presupuesto", presupuesto)

    # KPI sobre el dataset principal (sin `source`).
    rep.kpi("Ventas", operator="sum", expression=IMPORTE, format=CURRENCY)
    # KPI sobre el dataset secundario (`source=`).
    rep.kpi(
        "Presupuesto",
        operator="sum",
        column="presupuesto",
        source="presupuesto",
        format=CURRENCY,
    )

    rep.detail("agente", "sku", "cantidad", "precio", "descuento")

    save(rep.run(), "10_multi_dataset")


if __name__ == "__main__":
    main()
