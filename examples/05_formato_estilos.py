"""05 — Formato numérico y formato condicional por valor."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Formatos y estilos condicionales")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("fecha", "producto", "cantidad", "precio", "descuento", "importe")

    rep.set_format("precio", kind="currency", symbol="$", decimals=2, thousands=True)
    rep.set_format("importe", kind="currency", symbol="$", decimals=2, thousands=True)
    rep.set_format("descuento", kind="percent", decimals=0, percent_scale=True)
    rep.set_format("fecha", kind="date", pattern="%d/%m/%Y")

    rep.add_style("importe", when="gt", value=1000, color="#00aa77", bold=True)
    rep.add_style("descuento", when="gt", value=0.1, color="#cc0000")

    rep.group("global")
    rep.section("global").total("sum", "importe")

    save(rep.run(), "05_formato_estilos")


if __name__ == "__main__":
    main()
