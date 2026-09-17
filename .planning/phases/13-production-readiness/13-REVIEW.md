---
phase: 13-production-readiness
reviewed: 2026-09-17T10:30:00Z
depth: deep
files_reviewed: 7
files_reviewed_list:
  - encino_rpt/_serialize.py
  - encino_rpt/expressions.py
  - encino_rpt/models.py
  - encino_rpt/renderers/json.py
  - encino_rpt/report.py
  - encino_rpt/aggregation.py
  - encino_rpt/section.py
  - encino_rpt/charts.py
findings:
  critical: 0
  warning: 0
  info: 3
  total: 3
status: issues_found
---

# Phase 13: Code Review Report

**Reviewed:** 2026-09-17T10:30:00Z
**Depth:** deep
**Files Reviewed:** 8
**Status:** issues_found (solo hallazgos Info; sin bloqueadores ni warnings)

## Summary

Revisé el commit `956579d` (v1.4 "production readiness"): guard de `RecursionError` en
`to_jsonable`/`from_dict`, validación estricta de nodos en `_serialize._coerce`,
validación `Literal` en `__post_init__` de `Link`/`Format`/`Chart`/`ConditionalRule`, y
el catch de `ValueError` en `ast.parse` de `expressions.evaluate`.

Verifiqué cada uno de los cuatro puntos de foco con lectura de código, traza de call
chains a través de `report.py → aggregation.py → models.py/charts.py → renderers`, y
ejecución de casos de round-trip dirigidos:

1. **`_coerce` estricto**: rechaza correctamente `children` malformados (hijo no-dict
   → `ValueError("nodo hijo inválido…")`; `type` desconocido → `ValueError("tipo de nodo
   desconocido…")`) **sin** romper round-trips válidos. Confirmé con ejecución directa
   que `Format | None`, `dict[str, Format]` y `Detail.row` conteniendo una clave literal
   `"type"` hacen round-trip intactos. La clave `"type"` dentro de `Detail.row`
   (`dict[str, Any]`) no se confunde con el discriminador del nodo porque `_coerce` la
   trata con `Any` y devuelve el valor tal cual.
2. **Guard de `RecursionError`**: `to_dict`, `from_dict` y `to_json` convergen todos en
   rutas que ahora lanzan `ValueError(DEPTH_ERROR)`. `to_jsonable` (usado por `to_dict`
   y `JsonRenderer.to_dict`) y `from_dict` envuelven `RecursionError`. `JsonRenderer.render`
   conserva además un catch redundante de `RecursionError` sobre `json.dumps`
   (defensa en profundidad, inofensivo). `from_json` delega en `from_dict`, cubierto.
3. **`__post_init__`**: sin falsos positivos. El motor solo construye `Format` con
   `kind` ∈ {number, currency, percent, date} (validado en `set_format` y en
   `_as_format`), `ConditionalRule.when` ∈ {lt, le, gt, ge, eq, ne} (validado en
   `add_style`), `Chart.kind` ∈ {pie, bar, line} (único conjunto que los renderers
   conocen; `excel.py` usa `{pie, bar, line}`), y `Link.target` ∈ {section, report,
   page, external} (coincide con el docstring de `link()`). La suite completa (129 tests)
   pasa.
4. **`expressions.py`**: `ExpressionError` es subclase de `ValueError`, así que envolver
   el `ValueError` de `ast.parse` (null byte en 3.10) no enmascara ningún error legítimo:
   no cambia la jerarquía de excepciones (los callers que capturan `ValueError` siguen
   funcionando) y el único `ValueError` que `ast.parse` lanza es el de fuente inválida
   (null bytes), que correctamente es una "expresión no válida".

Sin bloqueadores ni warnings. Los tres hallazgos siguientes son observaciones de
calidad/mantenibilidad menores.

## Info

### IN-01: Validación de `Literal` duplicada/desfasada entre builder y modelo

**File:** `encino_rpt/report.py:274` (link), `encino_rpt/section.py:72` (chart), `encino_rpt/models.py:19,96`
**Issue:** `set_format`/`add_style` validan `kind`/`symbol_position`/`negative`/`when` en el
builder y tipan sus parámetros como `Literal`. En cambio `link()` (`target: str`) y
`Section.chart()` (`kind: str`) no validan ni tipan como `Literal`. Tras v1.4, un
`target`/`kind` inválido ya no falla al construir (fail-fast) sino en `run()`, con
superficies de error inconsistentes: `Link` lanza `ValueError` crudo desde `_build_link`
(sin contexto de columna) mientras `Chart` se envuelve en `AggregationError` vía `_wrap`.
**Fix:** Tipar `link(..., target: Literal["section","report","page","external"])` y
`chart(..., kind: Literal["pie","bar","line"])` y validar en el builder, manteniendo el
`__post_init__` como defensa en profundidad para la ruta `from_dict`/`format=` dict.

### IN-02: `from_dict` con `root` no-dict lanza `TypeError` poco claro

**File:** `encino_rpt/_serialize.py:113`
**Issue:** PRD-03 cubre hijos malformados con errores claros (`ValueError`), pero un
`root` que no sea dict (`from_dict({"root": 42})`) llega a `_build(Group, 42)` y lanza
`TypeError: argument of type 'int' is not iterable` (crudo y confuso). Es previo a este
commit, pero adyacente al objetivo "rechazar nodos malformados con error claro".
**Fix:** En `_build`, verificar `isinstance(data, dict)` antes de iterar campos y lanzar
`ValueError(f"se esperaba un dict para {cls.__name__}: {data!r}")`.

### IN-03: `Format.__post_init__` / `ConditionalRule.__post_init__` duplican la validación del builder

**File:** `encino_rpt/models.py:48,124`
**Issue:** Las reglas de `kind`/`symbol_position`/`negative` y `when` ya se validan en
`set_format` (`report.py:148-153`) y `add_style` (`report.py:185-186`). El `__post_init__`
las repite, creando dos fuentes de verdad (que pueden divergir en el futuro). Es inofensivo
y sí aporta para la ruta `format=` dict de `total()`/`kpi()` y para `from_dict`.
**Fix:** Ninguno requerido; si se desea, documentar el `__post_init__` como la única
fuente de verdad y hacer que los builders deleguen en él (lanzando en el builder para
fail-fast).

---

_Reviewed: 2026-09-17T10:30:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
