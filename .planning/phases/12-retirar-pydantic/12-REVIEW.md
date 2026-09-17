---
phase: 12-retirar-pydantic
reviewed: 2026-09-17T00:00:00Z
depth: deep
files_reviewed: 11
files_reviewed_list:
  - encino_rpt/models.py
  - encino_rpt/_serialize.py
  - encino_rpt/renderers/json.py
  - encino_rpt/aggregation.py
  - encino_rpt/report.py
  - encino_rpt/charts.py
  - encino_rpt/pivot.py
  - encino_rpt/section.py
  - encino_rpt/_specs.py
  - encino_rpt/renderers/_format.py
  - encino_rpt/renderers/_walk.py
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues
---

# Phase 12: Code Review Report — retirar pydantic

**Reviewed:** 2026-09-17
**Depth:** deep (cross-file: reconstrucción `from_dict`, coerción `to_jsonable`, sitios de construcción de modelos)
**Files Reviewed:** 11
**Status:** issues_found

## Summary

La migración de pydantic → `@dataclass` stdlib es **sólida en su camino crítico**. Verifiqué:

- **`to_jsonable`** reproduce el comportamiento de `model_dump(mode="json")` para los tipos que usa la librería: `Decimal→str`, `datetime/date/time→isoformat`, `Enum→value`, `tuple→list`, dataclass→dict (excluyendo campos `_privados`). No hay cambio silencioso de tipos respecto a pydantic v2 (pydantic v2 también serializa `Decimal` como `str` y `bytes` como base64).
- **`from_dict`** despacha correctamente la unión recursiva `Group.children` por el discriminador `type`; reconstruye `Format | None`, `dict[str, Format]`, `list[Series]`, `list[ConditionalRule]`, `ReportMeta`; y deja pasar sin tocar los `Any` de `Total.value`/`Detail.row`/`Pivot.cells`. El guard `node_cls in non_none` impide que un `dict[str, Any]` (p. ej. `Group.key` o `Detail.row` con una columna llamada `type`) sea mal reconstruido como nodo: `non_none` para `dict[str, Any]` solo contiene `dict[str, Any]`, nunca una dataclass de nodo. Verificado empíricamente: `key={"type": "detail"}` y `row={"type": "group"}` se conservan como dicts.
- **Reordenamiento de campos** (required-antes-de-default, que forzó mover `type` tras `target`/`href`/`src`/`row`/`kind`): **todos** los sitios de construcción usan argumentos por keyword (`Link(target=…)`, `Detail(row=…)`, `Group(name=…)`, `Format(**fmt)`, etc.). No hay construcción posicional que se rompa.
- **`__post_init__`** (`_first_row`/`_header_tpl`/`_footer_tpl`) se fijan correctamente; al ser atributos de instancia (no campos) quedan fuera de `to_jsonable`, `asdict`, `__eq__` y `__repr__`.

`pytest` (115 tests), `mypy` y `ruff` pasan. `uv.lock` ya no contiene pydantic (0 referencias).

Los dos **warnings** no rompen el round-trip primario (`to_dict()` → `from_dict()` siempre emite todas las claves), pero degradan robustez/contrato: se perdió la validación runtime de los `Literal` y el reconstructor pisa los `default_factory` con `None` ante claves ausentes.

## Warnings

### WR-01: Validación runtime de `Literal`/enum silenciosamente perdida

**File:** `encino_rpt/models.py:9-147` (todos los modelos), `encino_rpt/report.py:123-164`
**Issue:** Pydantic validaba los campos `Literal` en construcción (`Format(kind="bogus")` → `ValidationError`, igual para `when`, `symbol_position`, `negative`, `target`, `kind` de `Chart`, `type`, etc.). Con `@dataclass`, las anotaciones `Literal` son solo metadata para mypy: `Format(kind="bogus")` ahora se acepta silenciosamente. Verificado: `Format(kind="bogus").kind == "bogus"`. Para un reporteador financiero cuyo valor central es la **corrección**, un typo del usuario final (`kind="curreny"`) ya no falla temprano: `format_value` lo trata como `number` y el reporte sale sin símbolo de moneda, sin error. mypy solo protege a quien corre mypy (el propio repo), no al consumidor runtime de la librería.
**Fix:** Restaurar el fail-fast con validación explícita en `__post_init__`. Ejemplo mínimo y reutilizable:

```python
def _check_literal(obj: object, field_name: str, allowed: tuple[str, ...]) -> None:
    value = getattr(obj, field_name)
    if value not in allowed:
        raise ValueError(
            f"{type(obj).__name__}.{field_name}={value!r} debe ser uno de {allowed}"
        )

@dataclass
class Format:
    kind: Literal["number", "currency", "percent", "date"] = "number"
    ...
    def __post_init__(self):
        _check_literal(self, "kind", ("number", "currency", "percent", "date"))
        _check_literal(self, "symbol_position", ("prefix", "suffix"))
        _check_literal(self, "negative", ("minus", "paren"))
```

Aplicar igual a `Link.target`, `Chart.kind`, `ConditionalRule.when`, `Group.type`, `Detail.type`, `Chart.type`, `Pivot.type`, `Kpi.type`.

### WR-02: `from_dict` pisa los `default_factory` con `None` ante claves ausentes

**File:** `encino_rpt/_serialize.py:60-67`
**Issue:** `_build` hace `kwargs[f.name] = _coerce(data.get(f.name), hints[f.name])` para **todos** los campos `init`. Si una clave está ausente, `data.get` devuelve `None` y `_coerce(None, …)` devuelve `None`, que se pasa explícitamente a `cls(**kwargs)`, anulando el default. Verificado: `from_dict({"root": {...}})` produce `meta=None`, `columns=None`, `formats=None`, `styles=None`, `kpis=None` (deberían ser `ReportMeta()`, `[]`, `{}`). Un renderer que itere `result.columns` (html/csv/text lo hacen) reventaría con `TypeError: 'NoneType' object is not iterable`. Pydantic usaba los defaults. El round-trip de `to_dict()` no se ve afectado (siempre emite las 6 claves), pero `from_dict`/`from_json` son API pública y cualquier dict parcial (o JSON de una versión anterior del esquema) corrompe silenciosamente los defaults.
**Fix:** Omitir las claves ausentes para que aplique el `default_factory` del dataclass:

```python
def _build(cls: type, data: dict):
    hints = get_type_hints(cls)
    kwargs: dict[str, Any] = {}
    for f in dataclasses.fields(cls):
        if not f.init or f.name not in data:
            continue
        kwargs[f.name] = _coerce(data[f.name], hints[f.name])
    return cls(**kwargs)
```

## Info

### IN-01: Código muerto — `_discriminator()` sin usar

**File:** `encino_rpt/_serialize.py:53-57`
**Issue:** `_discriminator` está definida pero nunca se invoca; el despacho real lo hace `_NODES` + `_coerce`. Código muerto que confunde el mantenimiento.
**Fix:** Eliminar la función o usarla en `_coerce` si se pretende centralizar el discriminador.

### IN-02: `__eq__`/`__repr__`/`asdict` ya no reflejan los atributos privados (diferencia vs pydantic)

**File:** `encino_rpt/models.py:133-138`
**Issue:** Pydantic v2 compara `__dict__` en `__eq__`, por lo que dos `Group` con los mismos campos pero distinto `_first_row` eran desiguales; `@dataclass` compara solo campos (ignora `_first_row`/`_header_tpl`/`_footer_tpl`). No lo ejercita ningún test (la idempotencia compara `to_dict()`), pero es una diferencia de comportamiento observable si un consumidor compara instancias con `==`.
**Fix:** No requiere acción para el camino actual; documentar la semántica (o implementar `__eq__` propio si se desea preservar el comportamiento exacto de pydantic).

### IN-03: `bytes` ya no se coacciona (pydantic lo serializaba a base64)

**File:** `encino_rpt/_serialize.py:50`
**Issue:** `to_jsonable` devuelve `bytes` sin cambios; `json.dumps` lanzará `TypeError` sobre un `bytes`. Pydantic v2 lo serializaba como `str` base64 en `model_dump(mode="json")`. La librería no produce `bytes` en valores hoy, así que es de bajo impacto, pero es un cambio de contrato silencioso.
**Fix:** Si se desea paridad: `if isinstance(obj, bytes): return base64.b64encode(obj).decode("ascii")` (con `import base64`).

---

_Reviewed: 2026-09-17_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
