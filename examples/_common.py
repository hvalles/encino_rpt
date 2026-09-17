"""Utilidades compartidas por los ejemplos (rutas y guardado de salidas)."""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE / "data"
OUT = HERE / "output"


def save(result, name: str) -> None:
    """Guarda `result` en HTML/CSV/Markdown (+ Excel/PDF si los extras están instalados)."""
    OUT.mkdir(exist_ok=True)
    (OUT / f"{name}.html").write_text(result.render_html(), encoding="utf-8")
    (OUT / f"{name}.csv").write_text(result.to_csv(), encoding="utf-8")
    (OUT / f"{name}.md").write_text(result.to_markdown(), encoding="utf-8")
    try:
        ws = result.to_excel()
        ws.parent.save(OUT / f"{name}.xlsx")
    except ImportError:
        pass
    try:
        (OUT / f"{name}.pdf").write_bytes(result.to_pdf())
    except ImportError:
        pass
    print(f"guardado: {OUT / name}.html|csv|md[|xlsx|pdf]")
