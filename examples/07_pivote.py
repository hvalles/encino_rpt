"""07 — Pivote (cross-tab) región × producto."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Pivote región × producto")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("sku", "importe")

    rep.group("global")
    rep.section("global").pivot(
        "region",
        "producto",
        operator="sum",
        value_column="importe",
        title="Importe por región y producto",
    )

    save(rep.run(), "07_pivote")


if __name__ == "__main__":
    main()
