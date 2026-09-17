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

    def __init__(
        self,
        classes: dict | None = None,
        repeat_header: bool = False,
        *,
        css: bool = False,
        template: bool = False,
        title: str | None = None,
    ):
        self.classes = classes or {}
        self.repeat_header = repeat_header
        self.css = css
        self.template = template
        self.title = title

    def render(self, result) -> str:
        """Convierte el resultado a HTML.

        Args:
            result: El `ReportResult` a renderizar.

        Returns:
            La tabla HTML como cadena. Con `template=True`, el documento HTML
            completo (`<!DOCTYPE html>`, `<head>`, `<body class="report">`); el
            bloque `<style>` (si `css=True`) va dentro de `<head>`.
        """
        parts = ["<table>"]
        if result.columns:
            header = "".join(f"<th>{_esc(c)}</th>" for c in result.columns)
            parts.append(f"<thead><tr>{header}</tr></thead>")
        parts.append("<tbody>")
        self._walk(result.root, result, parts)
        parts.append("</tbody></table>")
        table = "".join(parts)

        if not self.template:
            style_block = _style_block(result) if self.css else ""
            return style_block + table

        title = _esc(self.title or result.meta.title or "")
        style_block = _style_block(result) if self.css else ""
        head = f'<meta charset="utf-8"><title>{title}</title>{style_block}'
        return (
            "<!DOCTYPE html><html><head>"
            + head
            + f'</head><body class="report">{table}</body></html>'
        )

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
                    attrs = self._cell_attrs(c, value, result)
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

    def _cell_attrs(self, column, value, result) -> str:
        matched = _matched_rules(column, value, result.styles)
        if self.css:
            if not matched:
                return ""
            return f' class="{" ".join(f"rpt-cond-{i}" for i in matched)}"'
        style: dict = {}
        for i in matched:
            style.update(result.styles[i].style)
        return _style_attr(style)


def _esc(text) -> str:
    return _html.escape(str(text))


def _matched_rules(column, value, rules) -> list[int]:
    matched: list[int] = []
    for i, r in enumerate(rules):
        if r.column is not None and r.column != column:
            continue
        if value is None:
            continue
        op = _OPS.get(r.when)
        if op is not None and op(value, r.value):
            matched.append(i)
    return matched


def _style_items(style) -> list[str]:
    if not style:
        return []
    items: list[str] = []
    for key, val in style.items():
        prop = key.replace("_", "-")
        if key == "bold":
            items.append("font-weight:bold" if val else "")
            continue
        if not _SAFE_PROP.match(prop):
            continue
        if val is True:
            items.append(prop)
        else:
            if isinstance(val, str) and _UNSAFE_VALUE.search(val):
                continue
            items.append(f"{prop}:{_esc(val)}")
    return [item for item in items if item]


def _style_attr(style) -> str:
    items = _style_items(style)
    return f' style="{";".join(items)}"' if items else ""


def _css_decls(style) -> str:
    return ";".join(_style_items(style))


def _style_block(result) -> str:
    rules = []
    for i, r in enumerate(result.styles):
        decls = _css_decls(r.style)
        if decls:
            rules.append(f".rpt-cond-{i}{{{decls}}}")
    if not rules:
        return ""
    return f"<style>{''.join(rules)}</style>"
