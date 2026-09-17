"""Renderer Markdown (tablas GFM, grupos como encabezados)."""

from __future__ import annotations

from ..models import Image, Link
from ._format import format_value
from ._walk import walk


def _md_escape(value) -> str:
    """Escapa `|` y saltos de línea para que un valor no rompa una tabla GFM."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _md_cell(value, fmt) -> str:
    """Convierte un valor de celda a Markdown (Link/Image, o texto escapado)."""
    if isinstance(value, Link):
        return f"[{value.label or value.href}]({value.href})"
    if isinstance(value, Image):
        return f"![{value.alt or ''}]({value.src})"
    return _md_escape(format_value(value, fmt))


def _md_table(headers, rows) -> str:
    """Construye una tabla GFM `| h1 | h2 |` + separador + filas ya escapadas."""
    head = "| " + " | ".join(_md_escape(str(h)) for h in headers) + " |"
    sep = "|" + "|".join("---" for _ in headers) + "|"
    body = [
        "| " + " | ".join("" if c is None else str(c) for c in row) + " |"
        for row in rows
    ]
    return "\n".join([head, sep, *body])


class MarkdownRenderer:
    """Renderiza el `ReportResult` a Markdown (tablas GFM, grupos como encabezados).

    Fidelidad limitada: sin formato condicional ni gráficos — los `Chart` degradan
    a una línea de texto resumen y los `Pivot` a una tabla GFM filas×columnas.
    """

    def render(self, result) -> str:
        """Convierte el resultado a Markdown.

        Args:
            result: El `ReportResult` a renderizar.

        Returns:
            El Markdown como cadena.
        """
        lines: list[str] = []
        for kpi in result.kpis:
            label = kpi.label or ""
            lines.append(f"**{label}:** {format_value(kpi.value, kpi.format)}")
        self._walk(result.root, result, lines)
        return "\n".join(lines)

    def _flush_pending(self, pending, result, lines):
        if not pending:
            return
        rows = [
            [_md_cell(row.get(c), result.formats.get(c)) for c in result.columns]
            for row in pending
        ]
        lines.append(_md_table(result.columns, rows))
        pending.clear()

    def _pivot_table(self, node) -> str:
        headers = [""] + [str(c) for c in node.columns]
        rows = []
        for i, row in enumerate(node.rows):
            cells = [_md_escape(row)]
            for v in node.cells[i]:
                cells.append("" if v is None else _md_escape(str(v)))
            rows.append(cells)
        return _md_table(headers, rows)

    def _walk(self, root, result, lines):
        depth = 0
        pending: list[dict] = []
        for event, node in walk(root):
            if event == "group_start":
                self._flush_pending(pending, result, lines)
                if node.header:
                    lines.append(f"{'#' * (depth + 2)} {node.header}")
                depth += 1
            elif event == "group_end":
                depth -= 1
                self._flush_pending(pending, result, lines)
                indent = "  " * depth
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (
                        result.formats.get(t.column) if t.column else None
                    )
                    lines.append(f"{indent}**{label}:** {format_value(t.value, fmt)}")
                if node.footer:
                    lines.append(f"{indent}{node.footer}")
            elif event == "detail":
                pending.append(node.row)
            elif event == "chart":
                self._flush_pending(pending, result, lines)
                if not node.series:
                    lines.append(f"**{node.title or ''}** ({node.kind})")
                else:
                    for s in node.series:
                        values = ", ".join(map(str, s.values))
                        lines.append(
                            f"**{node.title or ''}** ({node.kind}): "
                            f"{s.label or ''}: {values}"
                        )
            elif event == "pivot":
                self._flush_pending(pending, result, lines)
                lines.append(self._pivot_table(node))
