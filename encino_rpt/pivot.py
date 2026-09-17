"""Construcción de matrices filas x columnas (cross-tab / `Pivot`)."""

from __future__ import annotations

from typing import Any

from .models import Pivot


def build_pivot(spec, rows, value_fn) -> Pivot:
    """Construye un `Pivot` agrupando por `(row_column, column_column)`.

    - `rows`: renglones ya enriquecidos.
    - `value_fn(rows)`: agrega el operador sobre un conjunto de renglones.
    """
    row_values = _ordered_unique(
        _assert_hashable(spec.row_column, r.get(spec.row_column)) for r in rows
    )
    col_values = _ordered_unique(
        _assert_hashable(spec.column_column, r.get(spec.column_column)) for r in rows
    )
    row_index = {v: i for i, v in enumerate(row_values)}
    col_index = {v: i for i, v in enumerate(col_values)}

    buckets: dict[tuple[Any, Any], list[Any]] = {}
    row_buckets: dict[Any, list[Any]] = {}
    col_buckets: dict[Any, list[Any]] = {}
    for r in rows:
        rv = _assert_hashable(spec.row_column, r.get(spec.row_column))
        cv = _assert_hashable(spec.column_column, r.get(spec.column_column))
        buckets.setdefault((rv, cv), []).append(r)
        row_buckets.setdefault(rv, []).append(r)
        col_buckets.setdefault(cv, []).append(r)

    cells = [[None] * len(col_values) for _ in row_values]
    for (rv, cv), group in buckets.items():
        cells[row_index[rv]][col_index[cv]] = value_fn(group)

    row_totals = [value_fn(row_buckets[rv]) for rv in row_values]
    col_totals = [value_fn(col_buckets[cv]) for cv in col_values]

    return Pivot(
        title=spec.title,
        rows=row_values,
        columns=col_values,
        cells=cells,
        row_totals=row_totals,
        column_totals=col_totals,
        options=spec.options or {},
    )


def _ordered_unique(values):
    seen = set()
    out = []
    for v in values:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _assert_hashable(column, value):
    """Valida que `value` sea hashable (clave de agrupación del pivote).

    Lanza `ValueError` claro (nombrando la columna) en vez del `TypeError`
    crudo que produciría usarlo como clave de un `dict`/`set`.
    """
    try:
        hash(value)
    except TypeError as exc:
        raise ValueError(
            f"valor no hashable en la columna de pivote {column!r}: {value!r}"
        ) from exc
    return value
