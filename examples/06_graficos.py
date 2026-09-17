"""06 — Gráficos (pie/bar/line) derivados de los cortes."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Gráficos de ventas")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("sku", "importe")

    rep.group("por_region", columns="region")
    rep.section("por_region").total("sum", "importe")

    rep.group("global")
    rep.section("global").chart(
        "pie",
        title="Importe por región",
        operator="sum",
        column="importe",
        label_field="region",
    )
    rep.section("global").chart(
        "bar",
        title="Transacciones por región",
        operator="count",
        label_field="region",
    )

    save(rep.run(), "06_graficos")


if __name__ == "__main__":
    main()
