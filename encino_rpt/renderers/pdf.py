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
                rows.append([self._chart_drawing(node)])
                spans.append((0, len(rows) - 1, ncols - 1, len(rows) - 1))
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

    def _chart_drawing(self, node, width=460, height=200):
        """Construye un gráfico nativo de reportlab (`reportlab.graphics`)."""
        from reportlab.graphics.charts.barcharts import VerticalBarChart
        from reportlab.graphics.charts.linecharts import HorizontalLineChart
        from reportlab.graphics.charts.piecharts import Pie
        from reportlab.graphics.shapes import Drawing, String

        drawing = Drawing(width, height)
        values = [[_num(v) for v in s.values] for s in node.series]
        labels = [str(x) for x in node.labels]
        if node.title:
            drawing.add(String(8, height - 14, node.title))
        if node.kind == "pie" and values:
            pie = Pie()
            pie.x = 130
            pie.y = 6
            pie.width = height - 16
            pie.height = height - 16
            pie.data = values[0]
            pie.labels = labels
            drawing.add(pie)
        elif node.kind == "line" and values:
            lc = HorizontalLineChart()
            lc.x = 40
            lc.y = 30
            lc.width = width - 80
            lc.height = height - 60
            lc.data = values
            lc.categoryAxis.categoryNames = labels
            drawing.add(lc)
        elif values:
            bc = VerticalBarChart()
            bc.x = 40
            bc.y = 30
            bc.width = width - 80
            bc.height = height - 60
            bc.data = values
            bc.categoryAxis.categoryNames = labels
            drawing.add(bc)
        return drawing

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


def _num(value) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0
