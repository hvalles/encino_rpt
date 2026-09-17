"""Agregación: enriquece renglones, construye el árbol de grupos y resuelve totales."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from ._specs import GroupSpec
from .charts import build_chart
from .expressions import ExpressionError, evaluate
from .models import (
    Chart,
    Detail,
    Format,
    Group,
    Image,
    Kpi,
    Link,
    Pivot,
    ReportMeta,
    ReportResult,
    Total,
)
from .pivot import build_pivot
from .template import render as render_template

# Unión de nodos que pueblan `Group.children` (detail, subgrupo, chart, pivot).
Child = Detail | Group | Chart | Pivot


class AggregationError(ValueError):
    """Error de agregación con contexto (grupo/campo/fila)."""


def _wrap(context: str, fn, *args):
    """Ejecuta `fn(*args)` y re-lanza cualquier error con contexto legible."""
    try:
        return fn(*args)
    except AggregationError:
        raise
    except ExpressionError as exc:
        raise AggregationError(f"{context}: {exc}") from exc
    except Exception as exc:
        raise AggregationError(f"{context}: {type(exc).__name__}: {exc}") from exc


def _as_format(fmt):
    if fmt is None:
        return None
    if isinstance(fmt, Format):
        return fmt
    return Format(**fmt)


def _aggregate(operator, values):
    vals = [v for v in values if v is not None]
    if operator == "sum":
        return sum(vals)
    if operator == "avg":
        return (sum(vals) / len(vals)) if vals else None
    if operator == "count":
        return len(vals)
    if operator == "count_distinct":
        return len(set(vals))
    if operator == "max":
        return max(vals) if vals else None
    if operator == "min":
        return min(vals) if vals else None
    raise ValueError(f"operador desconocido: {operator!r}")


def _value_for(operator, column, expression, rows, functions, aggregates):
    """Calcula el valor de un agregado sobre `rows`.

    Semántica de `count`:
    - `count` sin `expression` y sin `column` cuenta filas (`len(rows)`).
    - `count` con `column` (sin `expression`) cuenta los valores no-`None` de
      esa columna.
    - `count` con `expression` es un conteo condicional: cuenta las filas cuya
      expresión evalúa *truthy* (las filas con resultado falsy —0, None, False—
      no se cuentan).
    """
    if operator.startswith("custom:"):
        name = operator.split(":", 1)[1]
        fn = aggregates.get(name)
        if fn is None:
            raise AggregationError(f"agregado custom no registrado: {name!r}")
        return fn(rows, column)
    if expression is not None:
        vals = [evaluate(expression, r, functions) for r in rows]
        if operator == "count":
            return sum(1 for v in vals if v)
        if operator == "count_distinct":
            return len({v for v in vals if v is not None})
        return _aggregate(operator, vals)
    if operator == "count" and column is None:
        return len(rows)
    vals = [r.get(column) for r in rows]
    return _aggregate(operator, vals)


def _make_total(spec, value):
    return Total(
        operator=spec.operator,
        column=spec.column,
        expression=spec.expression,
        name=spec.name,
        label=spec.label,
        value=value,
        format=_as_format(spec.format),
        column_position=spec.column_position,
        hidden=spec.hidden,
    )


def _make_value_fn(operator, column, expression, functions, aggregates):
    return lambda rows: _value_for(
        operator, column, expression, rows, functions, aggregates
    )


# --- enriquecimiento ---
def _build_link(spec, row):
    href = render_template(spec.href, row) if spec.href else ""
    label = render_template(spec.label, row) if spec.label else None
    return Link(target=spec.target, href=href, label=label)


def _build_image(spec, row):
    src = render_template(spec.src, row) if spec.src else ""
    alt = render_template(spec.alt, row) if spec.alt else None
    return Image(src=src, alt=alt, width=spec.width, height=spec.height)


def _enrich(report, source):
    rows = report._rows if source is None else report._datasets.get(source, [])
    out = []
    cum: dict[str, Any] = {}
    for index, row in enumerate(rows):
        enriched = dict(row)
        for f in report._fields:
            if f.source not in (None, source):
                continue
            if f.kind == "expr":
                if f.expression is None:
                    continue
                val = _wrap(
                    f"campo {f.name!r} (fila {index})",
                    evaluate,
                    f.expression,
                    enriched,
                    report._functions,
                )
                if f.cumulative == "sum":
                    prev = cum.get(f.name, 0 if f.start is None else f.start)
                    val = prev + (val or 0)
                    cum[f.name] = val
                enriched[f.name] = val
            elif f.kind == "link":
                enriched[f.name] = _build_link(f, enriched)
            elif f.kind == "image":
                enriched[f.name] = _build_image(f, enriched)
        out.append(enriched)
    return out


# --- árbol de grupos ---
def _build_group_tree(report):
    specs = report._groups
    root = None
    for name in report._order:
        s = specs[name]
        if s.columns is None and s.path is None:
            root = s
            break
    if root is None:
        root = GroupSpec(name="global", columns=None)

    children_map: dict[str, list[GroupSpec]] = {}
    for name in report._order:
        s = specs[name]
        if s is root:
            continue
        parent = specs.get(s.parent) if s.parent else None
        key = parent.name if parent is not None else root.name
        children_map.setdefault(key, []).append(s)
    return root, children_map


def _partition(spec, rows):
    if spec.columns is None:
        return [(None, list(rows))]
    index: dict[tuple[Any, ...], list[Any]] = {}
    order = []
    for r in rows:
        key = tuple(r.get(c) for c in spec.columns)
        try:
            hash(key)
        except TypeError as exc:
            for c in spec.columns:
                value = r.get(c)
                try:
                    hash(value)
                except TypeError:
                    raise ValueError(
                        f"valor no hashable en la columna de agrupación {c!r}: {value!r}"
                    ) from exc
            raise
        if key not in index:
            index[key] = []
            order.append(key)
        index[key].append(r)
    return [({c: v for c, v in zip(spec.columns, key)}, index[key]) for key in order]


def _build_group(
    report, spec, parent_rows, sources, registry, deferred, visible, children_map
):
    # Anidamiento: un corte parte las filas de su padre; solo usa su propio
    # `source` (multi-dataset) si lo declara.
    rows = parent_rows if spec.source is None else sources.get(spec.source, [])
    if spec.path is not None:
        return _build_path_group(report, spec, rows, registry, deferred, visible)
    result = []
    for key, part_rows in _partition(spec, rows):
        result.append(
            _build_instance(
                report,
                spec,
                key,
                part_rows,
                sources,
                registry,
                deferred,
                visible,
                children_map,
            )
        )
    return result


def _compute_totals_into(report, spec, rows, node, registry, deferred):
    for ts in spec.totals:
        if ts.expression and "TOTAL(" in ts.expression:
            total = _make_total(ts, None)
            deferred.append((total, ts, rows, spec.name))
            node.totals.append(total)
        else:
            val = _wrap(
                f"total {ts.name or ts.operator!r} (grupo {spec.name!r})",
                _value_for,
                ts.operator,
                ts.column,
                ts.expression,
                rows,
                report._functions,
                report._aggregates,
            )
            total = _make_total(ts, val)
            node.totals.append(total)
            if ts.name:
                key = f"{spec.name}.{ts.name}"
                # Un grupo vacío (total None) contribuye 0 al acumulado cruzado.
                registry[key] = registry.get(key, 0) + (val if val is not None else 0)


def _build_path_group(report, spec, rows, registry, deferred, visible):
    return _make_path_node(report, spec, rows, registry, deferred, visible)


def _segs(r, spec):
    return [s for s in str(r.get(spec.path, "")).split(spec.separator) if s != ""]


class _PathNode:
    """Nodo de un trie de rutas (jerarquía por `path` construida sin recursión)."""

    __slots__ = ("children", "leaf_rows", "order", "path", "rows")

    def __init__(self, path):
        self.path = path
        self.rows = []
        self.leaf_rows = []
        self.children = {}
        self.order = []


def _make_path_node(report, spec, rows, registry, deferred, visible):
    # dividir cada fila una sola vez (PERF-02)
    prepared = [(r, _segs(r, spec)) for r in rows]

    trie = _PathNode("")
    for r, segs in prepared:
        node = trie
        parts = []
        for seg in segs:
            parts.append(seg)
            child = node.children.get(seg)
            if child is None:
                child = _PathNode(spec.separator.join(parts))
                node.children[seg] = child
                node.order.append(seg)
            node = child
            node.rows.append(r)
        node.leaf_rows.append(r)

    # construir los Group iterativamente (sin límite de recursión por profundidad)
    groups = {}
    stack = [trie]
    while stack:
        tnode = stack.pop()
        if tnode is not trie:
            g = Group(
                name=spec.name,
                key={spec.path: tnode.path},
                show_collapsed=spec.show_collapsed,
                default_collapsed=spec.default_collapsed,
                page_break=spec.page_break,
            )
            g._first_row = dict(tnode.rows[0])
            g._header_tpl = spec.header
            g._footer_tpl = spec.footer
            _compute_totals_into(report, spec, tnode.rows, g, registry, deferred)
            groups[tnode] = g
        for seg in tnode.order:
            stack.append(tnode.children[seg])

    for tnode, g in groups.items():
        children: list[Child] = [
            Detail(row={k: v for k, v in r.items() if k in visible})
            for r in tnode.leaf_rows
        ]
        children += [groups[tnode.children[seg]] for seg in tnode.order]
        g.children = children

    return [(groups[trie.children[seg]], trie.children[seg].rows) for seg in trie.order]


def _build_instance(
    report, spec, key, rows, sources, registry, deferred, visible, children_map
):
    node = Group(
        name=spec.name,
        key=key,
        show_collapsed=spec.show_collapsed,
        default_collapsed=spec.default_collapsed,
        page_break=spec.page_break,
    )
    node._first_row = dict(rows[0]) if rows else {}
    node._header_tpl = spec.header
    node._footer_tpl = spec.footer

    # children: subgrupos o detalle
    child_pairs = []
    child_specs = children_map.get(spec.name, [])
    if child_specs:
        for child_spec in child_specs:
            child_pairs.extend(
                _build_group(
                    report,
                    child_spec,
                    rows,
                    sources,
                    registry,
                    deferred,
                    visible,
                    children_map,
                )
            )
        node.children = [n for n, _ in child_pairs]
    else:
        node.children = [
            Detail(row={k: v for k, v in r.items() if k in visible}) for r in rows
        ]

    # totals base + registro + diferidos
    _compute_totals_into(report, spec, rows, node, registry, deferred)

    # fase C sobre los hijos (grupos/detalle), antes de añadir chart/pivot
    node.children = _apply_order(spec, node.children, report._functions)

    # charts y pivots al final
    extras: list[Child] = []
    for cs in spec.charts:
        fn = _make_value_fn(
            cs.operator, cs.column, cs.expression, report._functions, report._aggregates
        )
        extras.append(
            _wrap(
                f"gráfico (grupo {spec.name!r})",
                build_chart,
                cs,
                child_pairs,
                node.totals,
                fn,
            )
        )
    for ps in spec.pivots:
        fn = _make_value_fn(
            ps.operator,
            ps.value_column,
            ps.value_expression,
            report._functions,
            report._aggregates,
        )
        extras.append(_wrap(f"pivote (grupo {spec.name!r})", build_pivot, ps, rows, fn))
    node.children = node.children + extras

    return node, rows


def _apply_order(spec, children, functions):
    if spec.order_by:
        ob = spec.order_by
        reverse = ob.get("direction") == "desc"
        children = sorted(
            children, key=lambda c: _sort_key(c, ob, functions), reverse=reverse
        )
    if spec.suppress_zero:
        sz = spec.suppress_zero
        children = [c for c in children if not _is_zero(c, sz)]
    if spec.top_n is not None:
        children = children[: spec.top_n]
    return children


def _child_desc(child) -> str:
    return (
        getattr(child, "name", None)
        or getattr(child, "key", None)
        or type(child).__name__
    )


def _sort_key(child, ob, functions):
    total = ob.get("total")
    expression = ob.get("expression")
    column = ob.get("column")
    if total:
        for t in getattr(child, "totals", []):
            if t.name == total:
                return t.value
        raise ValueError(
            f"total de orden inexistente: {total!r} (hijo {_child_desc(child)!r})"
        )
    if expression:
        return evaluate(expression, getattr(child, "_first_row", {}), functions)
    if column:
        if isinstance(child, Group):
            if child.key is None or column not in child.key:
                raise ValueError(
                    f"columna de orden inexistente: {column!r} (hijo {_child_desc(child)!r})"
                )
            return child.key[column]
        if isinstance(child, Detail):
            if column not in child.row:
                raise ValueError(
                    f"columna de orden inexistente: {column!r} (hijo {_child_desc(child)!r})"
                )
            return child.row[column]
        raise ValueError(
            f"columna de orden inexistente: {column!r} (hijo {_child_desc(child)!r})"
        )
    return 0


def _is_zero(child, sz):
    total = sz.get("total")
    column = sz.get("column")
    if total:
        for t in getattr(child, "totals", []):
            if t.name == total:
                return t.value is None or t.value == 0
        return False
    if column:
        if isinstance(child, Group):
            if child.key is None or column not in child.key:
                raise ValueError(
                    f"columna de suppress_zero inexistente: {column!r} "
                    f"(hijo {_child_desc(child)!r})"
                )
            v = child.key[column]
        elif isinstance(child, Detail):
            if column not in child.row:
                raise ValueError(
                    f"columna de suppress_zero inexistente: {column!r} "
                    f"(hijo {_child_desc(child)!r})"
                )
            v = child.row[column]
        else:
            raise ValueError(
                f"columna de suppress_zero inexistente: {column!r} "
                f"(hijo {_child_desc(child)!r})"
            )
        return v is None or v == 0
    return False


# --- fase B ---
def _resolve_deferred(deferred, functions, aggregates, registry):
    fns = dict(functions)
    fns["TOTAL"] = lambda name: registry.get(name)
    for total, spec, rows, group_name in deferred:
        total.value = _wrap(
            f"total {spec.name or spec.operator!r} (grupo {group_name!r})",
            _value_for,
            spec.operator,
            spec.column,
            spec.expression,
            rows,
            fns,
            aggregates,
        )


# --- plantillas (fase final) ---
def _render_templates(root, registry, params):
    from .renderers._format import format_value

    stack = [root]
    while stack:
        node = stack.pop()
        if not isinstance(node, Group):
            continue
        ctx = dict(node._first_row)
        if node.key:
            ctx.update(node.key)
        for t in node.totals:
            if t.name:
                ctx[f"total.{t.name}"] = format_value(t.value, t.format)
        for key, val in registry.items():
            ctx[f"total.{key}"] = val
        if node._header_tpl:
            node.header = render_template(node._header_tpl, ctx, params)
        if node._footer_tpl:
            node.footer = render_template(node._footer_tpl, ctx, params)
        stack.extend(node.children)


def _build_kpis(report, sources):
    kpis = []
    for spec in report._kpis:
        if spec.value is not None:
            value = spec.value
        else:
            rows = sources.get(spec.source, sources[None])
            value = _wrap(
                f"kpi {spec.label!r}",
                _value_for,
                spec.operator,
                spec.column,
                spec.expression,
                rows,
                report._functions,
                report._aggregates,
            )
        kpis.append(Kpi(label=spec.label, value=value, format=_as_format(spec.format)))
    return kpis


def _visible_columns(report):
    cols = list(report._detail)
    for f in report._fields:
        if f.after is not None and f.name not in cols:
            if f.after in cols:
                cols.insert(cols.index(f.after) + 1, f.name)
            else:
                cols.append(f.name)
    return cols


def _validate(report):
    known = set(report._datasets)
    for spec in report._groups.values():
        if spec.source is not None and spec.source not in known:
            raise ValueError(f"source no declarado: {spec.source!r}")
        if spec.parent is not None and spec.parent not in report._groups:
            raise ValueError(f"padre no declarado: {spec.parent!r}")
        for ts in spec.totals:
            if ts.operator.startswith("custom:"):
                name = ts.operator.split(":", 1)[1]
                if name not in report._aggregates:
                    raise AggregationError(f"agregado custom no registrado: {name!r}")
    for f in report._fields:
        if f.source is not None and f.source not in known:
            raise ValueError(f"source no declarado: {f.source!r}")
    if report._detail_source is not None and report._detail_source not in known:
        raise ValueError(f"source no declarado: {report._detail_source!r}")
    for k in report._kpis:
        if k.source is not None and k.source not in known:
            raise ValueError(f"source no declarado: {k.source!r}")


def build(report) -> ReportResult:
    _validate(report)
    visible = _visible_columns(report)
    visible_set = set(visible)

    sources = {None: _enrich(report, None)}
    for name in report._datasets:
        sources[name] = _enrich(report, name)

    root_spec, children_map = _build_group_tree(report)
    if report._detail_source is not None and children_map:
        raise ValueError(
            "`detail(source=...)` no es compatible con grupos; "
            "usa `group(..., source=...)`"
        )
    if report._detail_source is not None:
        root_spec = replace(root_spec, source=report._detail_source)
    registry: dict[str, Any] = {}
    deferred: list[tuple[Total, Any, Any, str]] = []
    root_nodes = _build_group(
        report,
        root_spec,
        sources[None],
        sources,
        registry,
        deferred,
        visible_set,
        children_map,
    )

    root = root_nodes[0][0] if root_nodes else Group(name="global", key=None)

    _resolve_deferred(deferred, report._functions, report._aggregates, registry)
    _render_templates(root, registry, report._params)

    return ReportResult(
        meta=ReportMeta(title=report._title, params=list(report._params)),
        columns=visible,
        formats=dict(report._formats),
        styles=list(report._styles),
        kpis=_build_kpis(report, sources),
        root=root,
    )
