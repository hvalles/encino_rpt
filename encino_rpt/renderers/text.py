"""Renderer de texto plano (inspección)."""

from __future__ import annotations

from collections.abc import Iterator

from ..models import Image, Link
from ._format import format_value
from ._walk import walk


class TextRenderer:
    """Renderiza el `ReportResult` a texto plano (para inspección)."""

    def render(self, result) -> str:
        """Convierte el resultado a texto plano.

        Args:
            result: El `ReportResult` a renderizar.

        Returns:
            El texto como cadena.
        """
        return "\n".join(self.iter_text(result))

    def iter_text(self, result) -> Iterator[str]:
        """Genera las líneas de texto del resultado, una por yield.

        Args:
            result: El `ReportResult` a renderizar.

        Yields:
            Cada línea de texto como `str`.
        """
        for kpi in result.kpis:
            yield f"{kpi.label}: {format_value(kpi.value, kpi.format)}"
        yield from self._walk_lines(result.root, result)

    def write(self, result, file) -> None:
        """Escribe el texto a un objeto file-like (streaming, línea por línea).

        Args:
            result: El `ReportResult` a renderizar.
            file: Objeto file-like con `write(str)`.
        """
        for i, line in enumerate(self.iter_text(result)):
            if i:
                file.write("\n")
            file.write(line)

    def _cell_text(self, value, fmt) -> str:
        if isinstance(value, Link):
            return f"{value.label or value.href} -> {value.href}"
        if isinstance(value, Image):
            return value.src
        return format_value(value, fmt)

    def _walk_lines(self, root, result) -> Iterator[str]:
        depth = 0
        for event, node in walk(root):
            if event == "group_start":
                if node.header:
                    yield f"{'  ' * depth}{node.header}"
                depth += 1
            elif event == "group_end":
                depth -= 1
                indent = "  " * depth
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (
                        result.formats.get(t.column) if t.column else None
                    )
                    yield f"{indent}{label}: {format_value(t.value, fmt)}"
                if node.footer:
                    yield f"{indent}{node.footer}"
            elif event == "detail":
                cells = "  ".join(
                    f"{c}={self._cell_text(node.row.get(c), result.formats.get(c))}"
                    for c in result.columns
                )
                yield f"{'  ' * depth}{cells}"
            elif event == "chart":
                yield f"{'  ' * depth}[chart:{node.kind}] {node.title or ''}"
                for s in node.series:
                    yield (
                        f"{'  ' * depth}  {s.label or ''}: "
                        f"{', '.join(map(str, s.values))}"
                    )
            elif event == "pivot":
                yield f"{'  ' * depth}[pivot] {node.title or ''}"
                yield f"{'  ' * depth}  (cols) {' '.join(map(str, node.columns))}"
                for i, row in enumerate(node.rows):
                    cells = " ".join("" if c is None else str(c) for c in node.cells[i])
                    yield f"{'  ' * depth}  {row}: {cells}"
