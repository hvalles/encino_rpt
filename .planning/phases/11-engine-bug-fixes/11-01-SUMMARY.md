---
phase: 11-engine-bug-fixes
plan: 01
subsystem: engine
tags: [pydantic, aggregation, correctness, error-handling, json-serialization]

# Dependency graph
requires:
  - phase: 8-tests-ci
    provides: [tests de regresión xfail que documentan los bugs (TEST-01)]
provides:
  - "fail-loudly en suppress_zero/agrupación no-hashable con ValueError claro"
  - "contexto de grupo en errores de chart/pivot (AggregationError)"
  - "guard de None en el registro de totales cruzados"
  - "semántica documentada de count (condicional truthy vs filas)"
  - "detail(source=) funcional a nivel raíz (incompatible con grupos)"
  - "serialización JSON profunda con ValueError controlado (no RecursionError)"
affects: [verification, phase-12+]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "_wrap() como frontera única para errores de chart/pivot con contexto"
    - "hash(value) up-front para validar claves de agrupación (no TypeError crudo)"
    - "dataclasses.replace para fijar el source raíz sin mutar el GroupSpec del usuario"

key-files:
  created: []
  modified:
    - encino_rpt/aggregation.py
    - encino_rpt/report.py
    - encino_rpt/pivot.py
    - encino_rpt/renderers/json.py
    - encino_rpt/models.py
    - tests/test_report.py
    - tests/test_report_renderers.py
    - docs/guide.md

key-decisions:
  - "CORR-08: detail(source=) solo a nivel raíz (opción b); con grupos lanza ValueError"
  - "CORR-09: un total None contribuye 0 al acumulado cruzado del registro"
  - "CORR-13: count + expression = conteo condicional (truthy); count sin expresión = filas"
  - "CORR-14: límite documentado + ValueError claro (no serialización iterativa)"

patterns-established:
  - "Mensajes de error con !r y nombre de columna/grupo (mismo patrón que _sort_key)"

requirements-completed: [CORR-08, CORR-09, CORR-10, CORR-11, CORR-12, CORR-13, CORR-14]

# Metrics
duration: 7min
completed: 2026-09-17
---

# Phase 11 Plan 01: Engine bug fixes (correctness) Summary

**Fail-loudly del motor: `suppress_zero`/agrupación no-hashable lanzan `ValueError` claro, chart/pivot ganan contexto de grupo, `detail(source=)` funciona a nivel raíz, `count` queda documentado como conteo condicional, y la serialización JSON profunda lanza `ValueError` controlado en vez de `RecursionError`.**

## Performance

- **Duration:** 7 min
- **Started:** 2026-09-17T13:42:55Z
- **Completed:** 2026-09-17T13:49:48Z
- **Tasks:** 5
- **Files modified:** 8

## Accomplishments

- Los 3 tests `xfail` de `tests/test_report.py` (`test_detail_source_ignored`, `test_named_total_none_values`, `test_chart_pivot_error_context`) pasaron a asserts verdes al corregir el bug correspondiente; los 2 tests de regresión que documentaban comportamiento actual (`test_suppress_zero_missing_column`, `test_unhashable_group_value`) ahora esperan `ValueError`.
- Errores de chart/pivot ahora se envuelven en `AggregationError` con contexto `"gráfico (grupo …)"`/`"pivote (grupo …)"` vía `_wrap`.
- `suppress_zero(column=…)` con columna inexistente y agrupación/pivote con valores no hashables lanzan `ValueError` claro nombrando la columna.
- `detail(source=…)` produce el detalle del dataset indicado a nivel raíz (sin grupos); combinado con `group()` lanza `ValueError`.
- `to_json()`/`model_dump` sobre jerarquías >1000 niveles lanzan `ValueError` controlado, no `RecursionError`.

## Task Commits

Each task was committed atomically:

1. **Task 1: CORR-10/11/12 (fail-loudly suppress_zero/no-hashable/chart-pivot)** - `cc48527` (fix)
2. **Task 2: CORR-09 (total None no rompe el registro)** - `3641d14` (fix)
3. **Task 3: CORR-13 (semántica de count)** - `1b3b097` (docs)
4. **Task 4: CORR-08 (detail(source=) raíz)** - `cd4a388` (fix)
5. **Task 5: CORR-14 (JSON profundo con ValueError)** - `6351bdd` (fix)

## Files Created/Modified

- `encino_rpt/aggregation.py` - `_wrap` en chart/pivot, `_is_zero` fail-loudly, `_partition` valida hash, `_compute_totals_into` guard de None, `_value_for` docstring, `detail(source=)` en `build()`/`_validate`
- `encino_rpt/report.py` - `_detail_source` + `detail()` almacena `source`
- `encino_rpt/pivot.py` - `_assert_hashable` + validación en `build_pivot`
- `encino_rpt/renderers/json.py` - `to_dict`/`render` envuelven `model_dump`/`json.dumps` con `ValueError` claro
- `encino_rpt/models.py` - docstring de `to_json` documenta el límite
- `tests/test_report.py` - xfail → asserts; nuevos asserts de `ValueError`
- `tests/test_report_renderers.py` - `test_deep_tree_to_json` espera mensaje claro
- `docs/guide.md` - nota del límite de profundidad JSON

## Decisions Made

- **CORR-08** (opción b confirmada): `detail(source=X)` aplica solo a nivel raíz (sin grupos); se implementa fijando el `source` del root spec vía `dataclasses.replace` (sin mutar el `GroupSpec` del usuario) y lanzando `ValueError` si hay `children_map` no vacío.
- **CORR-09**: `None` contribuye `0` al acumulado cruzado (`registry[key] = registry.get(key, 0) + (val if val is not None else 0)`).
- **CORR-13**: `count` sin expresión cuenta filas; `count` con expresión cuenta filas cuya evaluación es truthy (conteo condicional). Fijado en docstring de `_value_for` + test.
- **CORR-14**: límite documentado + `ValueError` claro (no serialización iterativa, inviable con pydantic).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Detección de no-hashable en `_partition` colocada en el punto correcto**
- **Found during:** Task 1 (CORR-12)
- **Issue:** El `try/except TypeError` inicial rodeaba la construcción de `tuple(...)`, pero `tuple(["a","b"],)` no lanza — el `TypeError` ocurre al hash **la clave** en `key not in index`.
- **Fix:** Validar `hash(key)` explícitamente antes de insertarla en el índice, y solo entonces identificar la columna culpable.
- **Files modified:** `encino_rpt/aggregation.py`
- **Verification:** `test_unhashable_group_value` pasa (ValueError con nombre de columna).
- **Committed in:** `cc48527` (Task 1 commit)

**2. [Rule 2 - Missing Critical] Test del caso "grupos + detail(source=)"**
- **Found during:** Task 4 (CORR-08)
- **Issue:** El criterio de aceptación exigía `ValueError` al combinar `detail(source=...)` con grupos, pero no existía test.
- **Fix:** Añadido `test_detail_source_with_groups_raises`.
- **Files modified:** `tests/test_report.py`
- **Verification:** `36 passed`.
- **Committed in:** `cd4a388` (Task 4 commit)

**3. [Rule 1 - Style] Colapso de `_wrap(pivote …)` a una línea**
- **Found during:** Task 5 (verificación final)
- **Issue:** `ruff format --check` pedía colapsar la llamada `_wrap` del pivote a una sola línea.
- **Fix:** Colapsada la línea; `ruff format --check encino_rpt tests` → "27 files already formatted".
- **Files modified:** `encino_rpt/aggregation.py`
- **Verification:** format check limpio.
- **Committed in:** `6351bdd` (Task 5 commit)

---

**Total deviations:** 3 auto-fixed (2 Rule 1, 1 Rule 2)
**Impact on plan:** Todas necesarias para correctitud/cobertura de aceptación. Sin scope creep.

## Issues Encountered

None - los fixes siguieron las decisiones confirmadas del contexto.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Los 7 bugs de correctitud de `CONCERNS.md` quedan corregidos con regresiones verdes.
- Suite completa: `113 passed`; `mypy encino_rpt` y `ruff check` limpios; `ruff format --check encino_rpt tests` limpio.
- Pendiente de verificación (verifier) del milestone v1.2.

---

*Phase: 11-engine-bug-fixes*
*Completed: 2026-09-17*

## Self-Check: PASSED

- Summary file present: `.planning/phases/11-engine-bug-fixes/11-01-SUMMARY.md`
- Task commits present: `cc48527`, `3641d14`, `1b3b097`, `cd4a388`, `6351bdd`
- Verification: `uv run pytest -q` → 113 passed; `mypy encino_rpt` → clean; `ruff check` → clean; `ruff format --check encino_rpt tests` → clean.
