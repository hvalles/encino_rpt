"""13 — Jerarquía por ruta (`path=`): cuentas contables anidadas."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Ventas por cuenta contable")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("sku", "producto", "importe")

    # La columna `cuenta` contiene rutas tipo "4.1.1"; se expanden en un árbol.
    rep.group("cuentas", path="cuenta")
    rep.section("cuentas").total("sum", "importe")

    rep.group("global")
    rep.section("global").total("sum", "importe")

    save(rep.run(), "13_jerarquia_path")


if __name__ == "__main__":
    main()
