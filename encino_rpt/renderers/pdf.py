"""Renderer PDF (reportlab, dependencia opcional)."""

from __future__ import annotations

import html as _html
import io
from typing import Any

from ..models import Image, Link
from ._format import format_value
from ._walk import walk


class PdfRenderer:
    """Renderiza el `ReportResult` a un PDF (reportlab)."""

    def render(
        self, result, repeat_header: bool = True, *, file=None, **opts
    ) -> bytes | None:
        """Convierte el resultado a PDF.

        Args:
            result: El `ReportResult` a renderizar.
            repeat_header: Repetir el encabezado de columnas en cada página.
            file: Objeto file-like binario (`.write(bytes)`). Si se provee, el PDF
                se escribe ahí (streaming) y devuelve `None`; si no, devuelve bytes.
            **opts: Opciones adicionales para `SimpleDocTemplate`.

        Returns:
            Los bytes del PDF, o `None` si se pasó `file`.

        Raises:
            ImportError: Si `reportlab` no está instalado.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Table,
                TableStyle,
            )
        except ImportError as exc:  # pragma: no cover - depende del entorno
            raise ImportError(
                "reportlab no está instalado; instala el extra `pdf`"
            ) from exc

        styles = getSampleStyleSheet()
        self._normal = styles["Normal"]

        buf = file if file is not None else io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, **opts)
        story = []

        if result.meta.title:
            story.append(Paragraph(_esc(result.meta.title), styles["Title"]))
        for kpi in result.kpis:
            story.append(
                Paragraph(
                    _esc(f"{kpi.label}: {format_value(kpi.value, kpi.format)}"),
                    styles["Normal"],
                )
            )

        rows: list[list[Any]] = []
        spans: list[tuple[int, int, int, int]] = []
        self._collect(result.root, result, rows, spans)

        if result.columns:
            header = [
                Paragraph(f"<b>{_esc(c)}</b>", styles["Normal"]) for c in result.columns
            ]
        else:
            header = [Paragraph("", styles["Normal"])]
        data = [header] + rows

        table = Table(data, repeatRows=1 if (repeat_header and result.columns) else 0)
        tstyle = [
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        for c1, r1, c2, r2 in spans:
            tstyle.append(("SPAN", (c1, r1 + 1), (c2, r2 + 1)))
        table.setStyle(TableStyle(tstyle))
        story.append(table)

        doc.build(story)
        if file is not None:
            return None
        return buf.getvalue()

    def _collect(self, root, result, rows, spans):
        ncols = len(result.columns) or 1
        for event, node in walk(root):
            if event == "group_start":
                if node.header:
                    self._full(node.header, rows, spans, ncols)
            elif event == "group_end":
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (
                        result.formats.get(t.column) if t.column else None
                    )
                    self._full(
                        f"{label}: {format_value(t.value, fmt)}", rows, spans, ncols
                    )
                if node.footer:
                    self._full(node.footer, rows, spans, ncols)
            elif event == "detail":
                rows.append(
                    [
                        self._cell(node.row.get(c), result.formats.get(c))
                        for c in result.columns
                    ]
                )
            elif event == "chart":
                summary = "; ".join(
                    f"{s.label or ''}: {', '.join(map(str, s.values))}"
                    for s in node.series
                )
                self._full(
                    f"{node.kind} {node.title or ''} — {summary}", rows, spans, ncols
                )
            elif event == "pivot":
                rows.append([self._pivot_table(node)])
                spans.append((0, len(rows) - 1, ncols - 1, len(rows) - 1))

    def _cell(self, value, fmt):
        from reportlab.platypus import Paragraph

        if isinstance(value, Link):
            return Paragraph(
                f'<a href="{_esc(value.href)}">{_esc(value.label or value.href)}</a>',
                self._normal,
            )
        if isinstance(value, Image):
            return Paragraph(_esc(value.src), self._normal)
        return format_value(value, fmt)

    def _full(self, text, rows, spans, ncols):
        from reportlab.platypus import Paragraph

        rows.append([Paragraph(f"<b>{_esc(text)}</b>", self._normal)])
        spans.append((0, len(rows) - 1, ncols - 1, len(rows) - 1))

    def _pivot_table(self, node):
        from reportlab.platypus import Paragraph, Table

        head = [Paragraph("", self._normal)] + [
            Paragraph(f"<b>{_esc(str(c))}</b>", self._normal) for c in node.columns
        ]
        data = [head]
        for i, r in enumerate(node.rows):
            cells = [Paragraph(_esc(str(r)), self._normal)]
            cells += [
                Paragraph(_esc("" if v is None else str(v)), self._normal)
                for v in node.cells[i]
            ]
            data.append(cells)
        return Table(data)


def _esc(text) -> str:
    return _html.escape(str(text))
