"""02 — Cortes anidados con encabezado, pie y totales por nivel."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Ventas por agente y región")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("sku", "producto", "cantidad", "precio", "importe")

    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente: {{agente}}")
    rep.section("por_agente").total("sum", "importe", label="Subtotal Agente")
    rep.section("por_agente").total("count", label="Transacciones")
    rep.section("por_agente").footer("Cierre de {{agente}}")

    rep.group("por_region", columns="region", parent="por_agente")
    rep.section("por_region").header("Región: {{region}}")
    rep.section("por_region").total("sum", "importe", label="Subtotal región")
    rep.section("por_region").footer("Cierre de {{region}}")

    rep.group("global")
    rep.section("global").header("Total general")
    rep.section("global").total("sum", "importe", name="total_gral")

    save(rep.run(), "02_grupos_totales")


if __name__ == "__main__":
    main()
