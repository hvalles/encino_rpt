"""Renderer CSV (aplanado)."""

from __future__ import annotations

import csv
import io

from ..models import Image, Link
from ._format import format_value
from ._sanitize import sanitize_csv
from ._walk import walk


class CsvRenderer:
    """Renderiza el `ReportResult` a CSV (aplanado)."""

    def __init__(self, delimiter: str = ","):
        self.delimiter = delimiter

    def render(self, result) -> str:
        """Convierte el resultado a CSV.

        Args:
            result: El `ReportResult` a renderizar.

        Returns:
            El CSV como cadena.
        """
        out = io.StringIO()
        writer = csv.writer(out, delimiter=self.delimiter)
        for kpi in result.kpis:
            writer.writerow([sanitize_csv(kpi.label), sanitize_csv(format_value(kpi.value, kpi.format))])
        self._walk(result.root, result, writer)
        return out.getvalue().rstrip("\r\n")

    def _cell_text(self, value, fmt) -> str:
        if isinstance(value, Link):
            return value.label or value.href
        if isinstance(value, Image):
            return value.src
        return format_value(value, fmt)

    def _walk(self, root, result, writer):
        for event, node in walk(root):
            if event == "group_start":
                if node.header:
                    writer.writerow([sanitize_csv(node.header)])
            elif event == "group_end":
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (result.formats.get(t.column) if t.column else None)
                    writer.writerow([sanitize_csv(label), sanitize_csv(format_value(t.value, fmt))])
                if node.footer:
                    writer.writerow([sanitize_csv(node.footer)])
            elif event == "detail":
                writer.writerow(
                    [sanitize_csv(self._cell_text(node.row.get(c), result.formats.get(c))) for c in result.columns]
                )
            elif event == "chart":
                writer.writerow([sanitize_csv(f"chart:{node.kind}"), sanitize_csv(node.title or "")])
                for s in node.series:
                    writer.writerow([sanitize_csv(s.label or ""), *[sanitize_csv(v) for v in s.values]])
            elif event == "pivot":
                writer.writerow(["", *[sanitize_csv(str(c)) for c in node.columns]])
                for i, row in enumerate(node.rows):
                    writer.writerow([sanitize_csv(row), *[sanitize_csv("" if c is None else c) for c in node.cells[i]]])
