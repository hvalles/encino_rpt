"""Renderer de texto plano (inspección)."""

from __future__ import annotations

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
        lines = []
        for kpi in result.kpis:
            lines.append(f"{kpi.label}: {format_value(kpi.value, kpi.format)}")
        self._walk(result.root, result, lines)
        return "\n".join(lines)

    def _cell_text(self, value, fmt) -> str:
        if isinstance(value, Link):
            return f"{value.label or value.href} -> {value.href}"
        if isinstance(value, Image):
            return value.src
        return format_value(value, fmt)

    def _walk(self, root, result, lines):
        depth = 0
        for event, node in walk(root):
            if event == "group_start":
                if node.header:
                    lines.append(f"{'  ' * depth}{node.header}")
                depth += 1
            elif event == "group_end":
                depth -= 1
                indent = "  " * depth
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (result.formats.get(t.column) if t.column else None)
                    lines.append(f"{indent}{label}: {format_value(t.value, fmt)}")
                if node.footer:
                    lines.append(f"{indent}{node.footer}")
            elif event == "detail":
                cells = "  ".join(
                    f"{c}={self._cell_text(node.row.get(c), result.formats.get(c))}"
                    for c in result.columns
                )
                lines.append(f"{'  ' * depth}{cells}")
            elif event == "chart":
                lines.append(f"{'  ' * depth}[chart:{node.kind}] {node.title or ''}")
                for s in node.series:
                    lines.append(f"{'  ' * depth}  {s.label or ''}: {', '.join(map(str, s.values))}")
            elif event == "pivot":
                lines.append(f"{'  ' * depth}[pivot] {node.title or ''}")
                lines.append(f"{'  ' * depth}  (cols) {' '.join(map(str, node.columns))}")
                for i, row in enumerate(node.rows):
                    cells = " ".join("" if c is None else str(c) for c in node.cells[i])
                    lines.append(f"{'  ' * depth}  {row}: {cells}")
