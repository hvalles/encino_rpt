"""01 — Tabla básica: detalle plano leído desde CSV."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Ventas — detalle")
    rep.detail("fecha", "agente", "region", "producto", "cantidad", "precio")
    save(rep.run(), "01_tabla_basica")


if __name__ == "__main__":
    main()
