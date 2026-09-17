"""03 — Campos calculados y saldo corrido (cumulative)."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Importe y saldo corrido")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.add_field("acumulado", "importe", after="importe", cumulative="sum")
    rep.detail("fecha", "agente", "sku", "cantidad", "precio", "importe", "acumulado")

    rep.group("global")
    rep.section("global").total("sum", "importe")

    save(rep.run(), "03_campos_calculados")


if __name__ == "__main__":
    main()
