"""Renderer CSV (aplanado)."""

from __future__ import annotations

import csv
import io

from ..models import Chart, Detail, Group, Pivot
from ._format import format_value
from ._sanitize import sanitize_csv


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

    def _walk(self, node, result, writer):
        if isinstance(node, Group):
            if node.header:
                writer.writerow([sanitize_csv(node.header)])
            for child in node.children:
                self._walk(child, result, writer)
            for t in node.totals:
                label = t.label or t.name or t.operator
                fmt = t.format or (result.formats.get(t.column) if t.column else None)
                writer.writerow([sanitize_csv(label), sanitize_csv(format_value(t.value, fmt))])
            if node.footer:
                writer.writerow([sanitize_csv(node.footer)])
        elif isinstance(node, Detail):
            writer.writerow(
                [sanitize_csv(format_value(node.row.get(c), result.formats.get(c))) for c in result.columns]
            )
        elif isinstance(node, Chart):
            writer.writerow([sanitize_csv(f"chart:{node.kind}"), sanitize_csv(node.title or "")])
            for s in node.series:
                writer.writerow([sanitize_csv(s.label or ""), *[sanitize_csv(v) for v in s.values]])
        elif isinstance(node, Pivot):
            writer.writerow(["", *[sanitize_csv(str(c)) for c in node.columns]])
            for i, row in enumerate(node.rows):
                writer.writerow([sanitize_csv(row), *[sanitize_csv("" if c is None else c) for c in node.cells[i]]])
