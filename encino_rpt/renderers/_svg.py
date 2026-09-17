"""Generación de gráficos SVG (Python puro) para el renderer HTML.

Sin dependencias ni JavaScript: emite SVG autocontenido para los gráficos
`pie`/`bar`/`line` del nodo `Chart`.
"""

from __future__ import annotations

import math

_PALETTE = [
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
]


def _num(value) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def _fmt(value) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _esc(text) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_chart_svg(node, width: int = 480, height: int = 280) -> str:
    """Genera el SVG de un nodo `Chart` según su `kind`."""
    if node.kind == "pie":
        return _pie(node, width, height)
    if node.kind == "bar":
        return _bar(node, width, height)
    return _line(node, width, height)


def _wrap(node, width, height, parts) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" class="chart-{node.kind}">'
        + "".join(parts)
        + "</svg>"
    )


def _title(node, width) -> str:
    if not node.title:
        return ""
    return (
        f'<text x="{width / 2:.0f}" y="20" font-size="14" font-weight="bold" '
        f'text-anchor="middle">{_esc(node.title)}</text>'
    )


def _pie(node, width, height) -> str:
    values = [_num(v) for v in (node.series[0].values if node.series else [])]
    labels = [str(x) for x in node.labels]
    total = sum(values) or 1.0
    cx = width * 0.35
    cy = height / 2
    radius = min(width * 0.6, height) / 2 - 20
    parts = [_title(node, width)]
    angle = -math.pi / 2
    for i, value in enumerate(values):
        frac = value / total
        end = angle + frac * 2 * math.pi
        color = _PALETTE[i % len(_PALETTE)]
        if frac >= 0.9999:
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius:.1f}" fill="{color}"/>'
            )
        else:
            x0 = cx + radius * math.cos(angle)
            y0 = cy + radius * math.sin(angle)
            x1 = cx + radius * math.cos(end)
            y1 = cy + radius * math.sin(end)
            large = 1 if (end - angle) > math.pi else 0
            parts.append(
                f'<path d="M{cx:.1f},{cy:.1f} L{x0:.1f},{y0:.1f} '
                f'A{radius:.1f},{radius:.1f} 0 {large} 1 {x1:.1f},{y1:.1f} Z" '
                f'fill="{color}"/>'
            )
        angle = end
    lx = width * 0.7
    ly = 44
    for i, (label, value) in enumerate(zip(labels, values)):
        color = _PALETTE[i % len(_PALETTE)]
        parts.append(
            f'<rect x="{lx:.0f}" y="{ly}" width="12" height="12" fill="{color}"/>'
        )
        parts.append(
            f'<text x="{lx + 18:.0f}" y="{ly + 11}" font-size="12">'
            f"{_esc(label)}: {_fmt(value)}</text>"
        )
        ly += 20
    return _wrap(node, width, height, parts)


def _axes(width, height, pad_l, pad_r, pad_t, pad_b) -> list[str]:
    return [
        f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{height - pad_b}" stroke="#999"/>',
        (
            f'<line x1="{pad_l}" y1="{height - pad_b}" x2="{width - pad_r}" '
            f'y2="{height - pad_b}" stroke="#999"/>'
        ),
    ]


def _series_values(node) -> list[list[float]]:
    return [[_num(v) for v in s.values] for s in node.series] or [[]]


def _bar(node, width, height) -> str:
    labels = [str(x) for x in node.labels]
    series = _series_values(node)
    pad_l, pad_r, pad_t, pad_b = 40, 20, 40, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    vmax = max([v for s in series for v in s] + [0.0]) or 1.0
    group_w = plot_w / max(len(labels), 1)
    bar_w = group_w / (len(series) + 1)
    parts = [_title(node, width), *_axes(width, height, pad_l, pad_r, pad_t, pad_b)]
    for i, label in enumerate(labels):
        gx = pad_l + i * group_w
        for j, s in enumerate(series):
            value = s[i] if i < len(s) else 0.0
            bh = (value / vmax) * plot_h
            x = gx + (j + 0.5) * bar_w
            color = _PALETTE[j % len(_PALETTE)]
            parts.append(
                f'<rect x="{x:.1f}" y="{height - pad_b - bh:.1f}" '
                f'width="{bar_w * 0.9:.1f}" height="{bh:.1f}" fill="{color}"/>'
            )
        parts.append(
            f'<text x="{gx + group_w / 2:.1f}" y="{height - pad_b + 14}" '
            f'font-size="11" text-anchor="middle">{_esc(label)}</text>'
        )
    return _wrap(node, width, height, parts)


def _line(node, width, height) -> str:
    labels = [str(x) for x in node.labels]
    series = _series_values(node)
    pad_l, pad_r, pad_t, pad_b = 40, 20, 40, 40
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    n = max(len(labels), 1)
    vmax = max([v for s in series for v in s] + [0.0]) or 1.0
    parts = [_title(node, width), *_axes(width, height, pad_l, pad_r, pad_t, pad_b)]
    step = plot_w / max(n - 1, 1)
    for j, s in enumerate(series):
        pts = []
        for i in range(n):
            value = s[i] if i < len(s) else 0.0
            x = pad_l + step * i
            y = height - pad_b - (value / vmax) * plot_h
            pts.append(f"{x:.1f},{y:.1f}")
        color = _PALETTE[j % len(_PALETTE)]
        parts.append(
            f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" '
            f'stroke-width="2"/>'
        )
    for i, label in enumerate(labels):
        x = pad_l + step * i
        parts.append(
            f'<text x="{x:.1f}" y="{height - pad_b + 14}" font-size="11" '
            f'text-anchor="middle">{_esc(label)}</text>'
        )
    return _wrap(node, width, height, parts)
