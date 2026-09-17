"""Renderer HTML (tabla con clases y formato condicional)."""

from __future__ import annotations

import html as _html
import re as _re

from ..models import Image, Link
from ._format import format_value
from ._walk import walk

_OPS = {
    "lt": lambda a, b: a < b,
    "le": lambda a, b: a <= b,
    "gt": lambda a, b: a > b,
    "ge": lambda a, b: a >= b,
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
}

_SAFE_PROP = _re.compile(r"^[a-zA-Z][a-zA-Z0-9-]*$")
_UNSAFE_VALUE = _re.compile(r"[;{}\x00-\x1f\x7f]")


class HtmlRenderer:
    """Renderiza el `ReportResult` a una tabla HTML con clases y formato condicional."""

    def __init__(self, classes: dict | None = None, repeat_header: bool = False):
        self.classes = classes or {}
        self.repeat_header = repeat_header

    def render(self, result) -> str:
        """Convierte el resultado a HTML.

        Args:
            result: El `ReportResult` a renderizar.

        Returns:
            La tabla HTML como cadena.
        """
        parts = ["<table>"]
        if result.columns:
            header = "".join(f"<th>{_esc(c)}</th>" for c in result.columns)
            parts.append(f"<thead><tr>{header}</tr></thead>")
        parts.append("<tbody>")
        self._walk(result.root, result, parts)
        parts.append("</tbody></table>")
        return "".join(parts)

    def _ncols(self, result) -> int:
        return len(result.columns) or 1

    def _walk(self, root, result, parts):
        for event, node in walk(root):
            if event == "group_start":
                if node.default_collapsed:
                    parts.append("<details>")
                    parts.append(f"<summary>{_esc(node.header or '')}</summary>")
                else:
                    if self.repeat_header and node.header and result.columns:
                        parts.append(self._header_row(result))
                    if node.header:
                        cls = "group page-break" if node.page_break else "group"
                        parts.append(
                            self._full_row(cls, node.header, self._ncols(result))
                        )
            elif event == "group_end":
                if node.default_collapsed:
                    parts.append("</details>")
                for t in node.totals:
                    label = t.label or t.name or t.operator
                    fmt = t.format or (
                        result.formats.get(t.column) if t.column else None
                    )
                    parts.append(
                        self._full_row(
                            "total",
                            f"{label}: {format_value(t.value, fmt)}",
                            self._ncols(result),
                        )
                    )
                if node.footer:
                    parts.append(
                        self._full_row("group", node.footer, self._ncols(result))
                    )
            elif event == "detail":
                cells = []
                for c in result.columns:
                    value = node.row.get(c)
                    attrs = self._cell_attrs(c, value, result.styles)
                    cells.append(
                        f"<td{attrs}>{self._cell_content(c, value, result)}</td>"
                    )
                parts.append(f"<tr>{''.join(cells)}</tr>")
            elif event == "chart":
                summary = "; ".join(
                    f"{s.label or ''}: {', '.join(map(str, s.values))}"
                    for s in node.series
                )
                parts.append(
                    self._full_row(
                        "chart",
                        f"{node.kind} {node.title or ''} — {summary}",
                        self._ncols(result),
                    )
                )
            elif event == "pivot":
                parts.append(
                    f'<tr class="pivot"><td colspan="{self._ncols(result)}">{self._pivot(node)}</td></tr>'
                )

    def _pivot(self, node) -> str:
        head = "<th></th>" + "".join(f"<th>{_esc(str(c))}</th>" for c in node.columns)
        rows = [f"<tr>{head}</tr>"]
        for i, r in enumerate(node.rows):
            cells = [f"<td>{_esc(str(r))}</td>"]
            cells += [
                f"<td>{'' if v is None else _esc(str(v))}</td>" for v in node.cells[i]
            ]
            rows.append(f"<tr>{''.join(cells)}</tr>")
        return f'<table class="pivot"><tbody>{"".join(rows)}</tbody></table>'

    def _full_row(self, css_class, text, ncols) -> str:
        cls = self.classes.get(css_class, css_class)
        return f'<tr class="{_esc(cls)}"><td colspan="{ncols}">{_esc(text)}</td></tr>'

    def _header_row(self, result) -> str:
        header = "".join(f"<th>{_esc(c)}</th>" for c in result.columns)
        return f'<tr class="header">{header}</tr>'

    def _cell_content(self, column, value, result) -> str:
        if isinstance(value, Link):
            href = _esc(value.href)
            label = _esc(value.label or value.href)
            return f'<a href="{href}">{label}</a>'
        if isinstance(value, Image):
            attrs = f' src="{_esc(value.src)}"'
            if value.alt is not None:
                attrs += f' alt="{_esc(value.alt)}"'
            if value.width is not None:
                attrs += f' width="{int(value.width)}"'
            if value.height is not None:
                attrs += f' height="{int(value.height)}"'
            return f"<img{attrs}/>"
        return _esc(format_value(value, result.formats.get(column)))

    def _cell_attrs(self, column, value, rules) -> str:
        style = {}
        for r in rules:
            if r.column is not None and r.column != column:
                continue
            if value is None:
                continue
            op = _OPS.get(r.when)
            if op is not None and op(value, r.value):
                style.update(r.style)
        return _style_attr(style)


def _esc(text) -> str:
    return _html.escape(str(text))


def _style_attr(style) -> str:
    if not style:
        return ""
    css = []
    for key, val in style.items():
        prop = key.replace("_", "-")
        if key == "bold":
            css.append("font-weight:bold" if val else "")
            continue
        if not _SAFE_PROP.match(prop):
            continue
        if val is True:
            css.append(prop)
        else:
            if isinstance(val, str) and _UNSAFE_VALUE.search(val):
                continue
            css.append(f"{prop}:{_esc(val)}")
    css = [c for c in css if c]
    return f' style="{";".join(css)}"' if css else ""
