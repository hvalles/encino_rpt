"""Serialización/deserialización del árbol canónico a dicts JSON (stdlib, sin pydantic)."""

from __future__ import annotations

import dataclasses
import types
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Union, get_args, get_origin, get_type_hints

from .models import Chart, Detail, Group, Pivot, ReportResult

_UNION = (Union, types.UnionType)

# Dispatch por el discriminador `type` en la unión recursiva de `Group.children`.
_NODES = {
    "group": Group,
    "detail": Detail,
    "chart": Chart,
    "pivot": Pivot,
}


def to_jsonable(obj: Any) -> Any:
    """Convierte el árbol (dataclasses) a tipos JSON nativos.

    Args:
        obj: Un `ReportResult` (u otro dataclass/nodo) o un valor simple.

    Returns:
        El equivalente JSON-nativo (`dict`/`list`/`str`/`int`/`float`/`bool`/`None`).
    """
    if isinstance(obj, dict):
        return {k: to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_jsonable(x) for x in obj]
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: to_jsonable(getattr(obj, f.name))
            for f in dataclasses.fields(obj)
            if not f.name.startswith("_")
        }
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    return obj


def _discriminator(cls: type) -> Any:
    for f in dataclasses.fields(cls):
        if f.name == "type":
            return f.default
    return None


def _build(cls: type, data: dict):
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in dataclasses.fields(cls):
        if not f.init:
            continue
        kwargs[f.name] = _coerce(data.get(f.name), hints[f.name])
    return cls(**kwargs)


def _coerce(value: Any, annotation: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(annotation)
    if origin in _UNION:
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if isinstance(value, dict):
            type_value = value.get("type")
            if isinstance(type_value, str):
                node_cls = _NODES.get(type_value)
                if node_cls is not None and node_cls in non_none:
                    return _build(node_cls, value)
            dataclass_candidates = [
                a
                for a in non_none
                if isinstance(a, type) and dataclasses.is_dataclass(a)
            ]
            if len(dataclass_candidates) == 1:
                return _build(dataclass_candidates[0], value)
        return value
    if origin is list:
        item_t = (get_args(annotation) or (Any,))[0]
        return [_coerce(x, item_t) for x in value]
    if origin is dict:
        vt = (get_args(annotation) or (Any, Any))[1]
        return {k: _coerce(v, vt) for k, v in value.items()}
    if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
        return _build(annotation, value)
    return value


def from_dict(data: dict) -> ReportResult:
    """Reconstruye un `ReportResult` a partir de un dict (round-trip de `to_dict`).

    Args:
        data: Dict producido por `to_dict()`.

    Returns:
        El `ReportResult` reconstruido.
    """
    return _build(ReportResult, data)
