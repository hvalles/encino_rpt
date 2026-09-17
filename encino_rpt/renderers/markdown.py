"""Renderer Markdown (tablas GFM, grupos como encabezados)."""

from __future__ import annotations

from collections.abc import Iterator

from ..models import Image, Link
from ._format import format_value
from ._walk import walk


def _md_escape(value) -> str:
    """Escapa `|` y saltos de línea para que un valor no rompa una tabla GFM."""
    return str(value).replace("|", "\\|").replace("\n", " ")


def _md_url(value) -> str:
    """Escapa una URL/atributo para `[](...)`/`![](...)` (tabla GFM + paréntesis)."""
    return (
        str(value)
        .replace("|", "\\|")
        .replace("\n", " ")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def _md_cell(value, fmt) -> str:
    """Convierte un valor de celda a Markdown (Link/Image, o texto escapado)."""
    if isinstance(value, Link):
        return f"[{_md_escape(value.label or value.href)}]({_md_url(value.href)})"
    if isinstance(value, Image):
        return f"![{_md_escape(value.alt or '')}]({_md_url(value.src)})"
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
        return "\n".join(self.iter_markdown(result))

    def iter_markdown(self, result) -> Iterator[str]:
        """Genera las líneas Markdown del resultado, una por yield.

        Args:
            result: El `ReportResult` a renderizar.

        Yields:
            Cada línea Markdown como `str`.
        """
        for kpi in result.kpis:
            label = kpi.label or ""
            yield f"**{label}:** {format_value(kpi.value, kpi.format)}"
        yield from self._walk_lines(result.root, result)

    def write(self, result, file) -> None:
        """Escribe el Markdown a un objeto file-like (streaming, línea por línea).

        Args:
            result: El `ReportResult` a renderizar.
            file: Objeto file-like con `write(str)`.
        """
        for i, line in enumerate(self.iter_markdown(result)):
            if i:
                file.write("\n")
            file.write(line)

    def _flush_pending(self, pending, result) -> Iterator[str]:
        if not pending:
            return
        rows = [
            [_md_cell(row.get(c), result.formats.get(c)) for c in result.columns]
            for row in pending
        ]
        yield _md_table(result.columns, rows)
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

    def _walk_lines(self, root, result) -> Iterator[str]:
        depth = 0
        pending: list[dict] = []
        for event, node in walk(root):
            if event == "group_start":
                yield from self._flush_pending(pending, result)
                if node.header:
                    yield f"{'#' * (depth + 2)} {node.header}"
                depth += 1
            elif event == "group_end":
                depth -= 1
                yield from self._flush_pending(pending, result)
                indent = "  " * depth
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (
                        result.formats.get(t.column) if t.column else None
                    )
                    yield f"{indent}**{label}:** {format_value(t.value, fmt)}"
                if node.footer:
                    yield f"{indent}{node.footer}"
            elif event == "detail":
                pending.append(node.row)
            elif event == "chart":
                yield from self._flush_pending(pending, result)
                if not node.series:
                    yield f"**{node.title or ''}** ({node.kind})"
                else:
                    for s in node.series:
                        values = ", ".join(map(str, s.values))
                        yield (
                            f"**{node.title or ''}** ({node.kind}): "
                            f"{s.label or ''}: {values}"
                        )
            elif event == "pivot":
                yield from self._flush_pending(pending, result)
                yield self._pivot_table(node)
