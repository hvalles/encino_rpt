---
phase: 11-engine-bug-fixes
reviewed: 2026-09-17T08:00:00Z
depth: deep
files_reviewed: 4
files_reviewed_list:
  - encino_rpt/aggregation.py
  - encino_rpt/report.py
  - encino_rpt/pivot.py
  - encino_rpt/renderers/json.py
findings:
  critical: 0
  major: 1
  minor: 1
  info: 1
  total: 3
status: issues
---

# Phase 11: Code Review Report — engine bug fixes

**Reviewed:** 2026-09-17
**Depth:** deep (cross-file call-chain tracing)
**Files Reviewed:** 4 (`aggregation.py`, `report.py`, `pivot.py`, `renderers/json.py`; además revisé `_specs.py`, `charts.py`, `expressions.py` y `models.py` para trazar las llamadas)
**Status:** issues

## Summary

Revisé los 5 commits de la fase 11 (`cc48527`, `3641d14`, `1b3b097`, `cd4a388`, `6351bdd`) contra los 5 focos solicitados. La corrección de los 7 bugs (CORR-08 a CORR-14) es **en general correcta**:

- **CORR-11** (`_is_zero` fail-loudly) replica exactamente el patrón de `_sort_key` (misma estructura de `ValueError`, misma columna `{column!r}` y `hijo {_child_desc(child)!r}`). Sin regresión para inputs válidos: solo convierte un *silent-wrong* (suprimir todo por columna ausente) en un error claro.
- **CORR-12** (`_partition`/`build_pivot` no-hashable) valida `hash(...)` up-front y nombra la columna culpable. El `raise` de respaldo tras el bucle es inalcanzable en la práctica (defensivo, inofensivo).
- **CORR-10** (`_wrap` en chart/pivot) envuelve correctamente; `build_chart` llama a `value_fn` que a su vez llama a `evaluate`, cuyo `ZeroDivisionError`/`ExpressionError` queda capturado por `_wrap` con contexto `"gráfico (grupo '…')"`.
- **CORR-09** (guard de `None` en el registro) suma `0` solo en el acumulado (`registry[key]`), preservando `Total.value = None` en el nodo emitido. El test `test_named_total_none_values` lo ejercita (antes `0 + None` → `TypeError`).
- **CORR-08** (`detail(source=)`) fija el `source` del root spec vía `dataclasses.replace` (sin mutar el `GroupSpec` del usuario) y el detalle raíz efectivamente proviene del dataset correcto (`sources.get(spec.source, sources[None])`). El `ValueError` de incompatibilidad con grupos se dispara antes del `replace`.

Sin embargo, hay **un defecto real en el manejo de errores de `json.py`** (CORR-14) que contradice el propio objetivo del fix, y una imprecisión en el docstring de `count`. Detalle abajo.

Verificación empírica realizada: `uv run pytest tests/test_report.py tests/test_report_renderers.py -q` → **79 passed**.

## Major

### MA-01: `to_dict` atrapa `ValueError` de forma demasiado amplia y relabela errores de serialización legítimos como "jerarquía demasiado profunda"

**File:** `encino_rpt/renderers/json.py:46-49`
**Issue:** `to_dict` envuelve `result.model_dump(mode="json")` en `except (RecursionError, ValueError)`. pydantic v2 lanza `pydantic_core.PydanticSerializationError` — que **hereda de `ValueError`** — para valores no serializables a JSON (p. ej. un tipo desconocido dentro de `Detail.row`). Al capturar todo `ValueError`, ese error se relabela como "la jerarquía es demasiado profunda para serializar a JSON", ocultando la causa real. El objetivo del CORR-14 era dar un error *claro*, no enmascarar otros errores.

Reproducción confirmada:
```python
from encino_rpt import Report
rep = Report([{"sku": object(), "monto": 10}])
rep.detail("sku", "monto"); rep.group("global")
rep.run().to_json()
# ValueError: la jerarquía es demasiado profunda para serializar a JSON...
# (cuando el error real es: Unable to serialize unknown type: <class 'object'>)
```

**Fix:** Limitar la captura al error de profundidad (el mensaje de pydantic es `"Circular reference detected (depth exceeded)"`), re-lanzando cualquier otro `ValueError` sin alterar:
```python
try:
    data = result.model_dump(mode="json")
except RecursionError as exc:
    raise ValueError(_DEPTH_ERROR) from exc
except ValueError as exc:
    # Solo relabelar el error de profundidad de pydantic; otros ValueError
    # (p. ej. PydanticSerializationError) deben propagarse intactos.
    if "depth" in str(exc):
        raise ValueError(_DEPTH_ERROR) from exc
    raise
```

## Minor

### MI-01: Docstring de `_value_for` sobregeneraliza la semántica de `count`

**File:** `encino_rpt/aggregation.py:74-78`
**Issue:** El primer bullet dice "`count` sin `expression` cuenta filas (`len(rows)`)". Eso solo es cierto cuando además `column is None`. Con `count` + `column` (sin `expression`) el código cae a `_aggregate("count", vals)`, que **filtra `None`** y cuenta valores no-None, no `len(rows)`.

Confirmado empíricamente:
```python
total("count", column="monto", name="no_null")  # filas [10, None, 5] -> 2, no 3
```
El docstring debe reflejar las tres ramas reales de `_value_for`.

**Fix:**
```python
Semántica de `count`:
- `count` sin `expression` y sin `column` cuenta filas (`len(rows)`).
- `count` con `column` (sin `expression`) cuenta los valores no-None de esa
  columna (`_aggregate` filtra `None`).
- `count` con `expression` es un conteo condicional: cuenta las filas cuya
  expresión evalúa *truthy* (las filas con resultado falsy —0, None, False—
  no se cuentan).
```

## Info

### IN-01: Import perezoso de `dataclasses.replace` dentro de `build()`

**File:** `encino_rpt/aggregation.py:599`
**Issue:** `from dataclasses import replace` se importa dentro de `build()` en lugar de a nivel de módulo. `dataclasses` es stdlib (sin riesgo de ciclo ni costo de import), y el resto del módulo importa en el tope (`from ._specs import ...`, etc.). Es solo un desvío de estilo del patrón del repo; no es un bug.

**Fix:** Mover `from dataclasses import replace` al bloque de imports del tope de `aggregation.py` junto a los demás `import`/`from`, dejando `build()` limpio.

---

_Reviewed: 2026-09-17_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
