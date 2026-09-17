"""02 — Cortes anidados con encabezado y pie; el total va dentro del footer."""

from _common import DATA, save

from encino_rpt import Report

CURRENCY = {"kind": "currency", "symbol": "$", "decimals": 2, "thousands": True}


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Ventas por agente y región")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("sku", "producto", "cantidad", "precio", "importe")

    # Total oculto: se calcula y se referencia en el footer, sin fila propia.
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente: {{agente}}")
    rep.section("por_agente").total(
        "sum", "importe", name="subtotal_agente", hidden=True, format=CURRENCY
    )
    rep.section("por_agente").footer("Cierre de {{agente}}: {{total.subtotal_agente}}")

    rep.group("por_region", columns="region", parent="por_agente")
    rep.section("por_region").header("Región: {{region}}")
    rep.section("por_region").total(
        "sum", "importe", name="subtotal_region", hidden=True, format=CURRENCY
    )
    rep.section("por_region").footer("Cierre de {{region}}: {{total.subtotal_region}}")

    rep.group("global")
    rep.section("global").header("Total general")
    rep.section("global").total("sum", "importe", name="total_gral", format=CURRENCY)
    rep.section("global").total("count", label="Transacciones")

    save(rep.run(), "02_grupos_totales")


if __name__ == "__main__":
    main()
