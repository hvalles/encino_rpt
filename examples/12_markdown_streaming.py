"""12 — Salida Markdown y streaming de salida (`iter_*` / `file=`)."""

from _common import DATA, OUT, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Markdown y streaming")
    rep.add_field("importe", "cantidad * precio * (1 - descuento)", after="precio")
    rep.detail("agente", "sku", "importe")
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "importe")

    result = rep.run()
    save(result, "12_markdown_streaming")

    # Streaming: escribir el CSV a un archivo sin materializar la cadena completa.
    OUT.mkdir(exist_ok=True)
    with (OUT / "12_stream.csv").open("w", encoding="utf-8") as fh:
        result.to_csv(file=fh)

    # `iter_*` permite consumir la salida por fragmentos.
    primera_linea = next(result.iter_csv())
    print(f"primera línea CSV: {primera_linea}")


if __name__ == "__main__":
    main()
