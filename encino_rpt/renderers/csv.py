"""Renderer CSV (aplanado)."""

from __future__ import annotations

import csv
import io
from collections.abc import Iterator

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
        return "\n".join(self.iter_csv(result))

    def iter_csv(self, result) -> Iterator[str]:
        """Genera las líneas CSV (sin terminador) del resultado, una por yield.

        Args:
            result: El `ReportResult` a renderizar.

        Yields:
            Cada línea CSV como `str` (sin `\\n`/`\\r\\n` final).
        """
        for row in self._iter_rows(result):
            yield self._line(row)

    def write(self, result, file) -> None:
        """Escribe el CSV a un objeto file-like (streaming, línea por línea).

        Args:
            result: El `ReportResult` a renderizar.
            file: Objeto file-like con `write(str)`.
        """
        for i, line in enumerate(self.iter_csv(result)):
            if i:
                file.write("\n")
            file.write(line)

    def _line(self, row) -> str:
        buf = io.StringIO()
        csv.writer(buf, delimiter=self.delimiter, lineterminator="").writerow(row)
        return buf.getvalue()

    def _cell_text(self, value, fmt) -> str:
        if isinstance(value, Link):
            return value.label or value.href
        if isinstance(value, Image):
            return value.src
        return format_value(value, fmt)

    def _iter_rows(self, result) -> Iterator[list]:
        for kpi in result.kpis:
            yield [
                sanitize_csv(kpi.label),
                sanitize_csv(format_value(kpi.value, kpi.format)),
            ]
        yield from self._walk_rows(result.root, result)

    def _walk_rows(self, root, result) -> Iterator[list]:
        for event, node in walk(root):
            if event == "group_start":
                if node.header:
                    yield [sanitize_csv(node.header)]
            elif event == "group_end":
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (
                        result.formats.get(t.column) if t.column else None
                    )
                    yield [
                        sanitize_csv(label),
                        sanitize_csv(format_value(t.value, fmt)),
                    ]
                if node.footer:
                    yield [sanitize_csv(node.footer)]
            elif event == "detail":
                yield [
                    sanitize_csv(
                        self._cell_text(node.row.get(c), result.formats.get(c))
                    )
                    for c in result.columns
                ]
            elif event == "chart":
                yield [
                    sanitize_csv(f"chart:{node.kind}"),
                    sanitize_csv(node.title or ""),
                ]
                for s in node.series:
                    yield [
                        sanitize_csv(s.label or ""),
                        *[sanitize_csv(v) for v in s.values],
                    ]
            elif event == "pivot":
                yield ["", *[sanitize_csv(str(c)) for c in node.columns]]
                for i, row in enumerate(node.rows):
                    yield [
                        sanitize_csv(row),
                        *[sanitize_csv("" if c is None else c) for c in node.cells[i]],
                    ]
