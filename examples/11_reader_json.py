"""11 — Readers: `Report.read` resuelve el formato por extensión y auto-detecta tipos."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    # JSON: el formato se resuelve por la extensión `.json`.
    rep = Report.read(DATA / "presupuesto.json", title="Presupuesto por agente")
    rep.detail("agente", "presupuesto")
    rep.group("global")
    rep.section("global").total("sum", "presupuesto")
    save(rep.run(), "11_reader_json")

    # CSV con `coerce=False`: todos los valores quedan como texto (control total).
    raw = Report.read(DATA / "ventas.csv", coerce=False, title="CSV sin coerción")
    raw.detail("fecha", "agente", "cantidad")
    save(raw.run(), "11_reader_csv_raw")


if __name__ == "__main__":
    main()
