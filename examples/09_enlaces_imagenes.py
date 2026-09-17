"""09 — Celdas enriquecidas: enlaces e imágenes."""

from _common import DATA, save

from encino_rpt import Report


def main() -> None:
    rep = Report.read(DATA / "ventas.csv", title="Enlaces e imágenes")
    rep.link(
        "pedido",
        "external",
        href="https://example.com/pedido/{{sku}}",
        label="Ver pedido",
        after="sku",
    )
    rep.image(
        "icono",
        "https://example.com/img/{{sku}}.png",
        alt="Ícono {{sku}}",
        width=24,
        height=24,
        after="producto",
    )
    rep.detail("fecha", "agente", "sku", "pedido", "producto", "icono")

    save(rep.run(), "09_enlaces_imagenes")


if __name__ == "__main__":
    main()
