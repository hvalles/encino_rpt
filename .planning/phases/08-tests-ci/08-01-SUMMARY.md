---
phase: 08-tests-ci
plan: 01
subsystem: testing
tags: [pytest, regression-tests, xfail, aggregation-engine]

# Dependency graph
requires:
  - phase: 07-refactor
    provides: shared traversal + immutable GroupSpec (engine surface under test)
provides:
  - 7 tests de regresión TEST-01 en tests/test_report.py (4 comportamiento-actual + 3 xfail(strict=True))
affects: [08-tests-ci (08-02, 08-03, 08-04), verifier]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Regresión de bugs no-corregidos con assert del comportamiento actual + comentario español `# CONCERNS.md`"
    - "Regresión de bugs con comportamiento-correcto definido vía `@pytest.mark.xfail(strict=True, reason=...)`"

key-files:
  created: []
  modified: [tests/test_report.py]

key-decisions:
  - "Los 3 bugs con comportamiento-correcto definido (detail source, totales None, errores chart/pivot) se documentan como xfail(strict=True), no como asserts del comportamiento roto"
  - "Los 4 bugs sin comportamiento-correcto definido se documentan con assert del comportamiento actual + comentario `# CONCERNS.md`"

patterns-established:
  - "Bug conocido (comportamiento actual): assert directo + comentario `# regresión documenta bug conocido — ver CONCERNS.md §...`"
  - "Bug conocido (comportamiento correcto): `@pytest.mark.xfail(strict=True, reason=\"bug conocido — ver CONCERNS.md §...\")`"

requirements-completed: []  # TEST-01 no se marca completo aquí: abarca 08-01 y 08-02 (renderers/seguridad + smoke de rendimiento pendientes)

# Metrics
duration: 8min
completed: 2026-09-17
---

# Phase 08 Plan 01: Tests & CI Summary

**7 tests de regresión TEST-01 en `tests/test_report.py` — multi-dataset, suppress_zero, totales None, valores no-hashables, `detail(source=)`, semántica de `count` y errores chart/pivot (3 `xfail(strict=True)`)**

## Performance

- **Duration:** 8 min
- **Started:** 2026-09-17T03:46:00Z
- **Completed:** 2026-09-17T03:54:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- 7 tests de regresión nuevos consolidan la superficie de regresión del motor de agregación (`TEST-01`).
- 4 bugs sin comportamiento-correcto definido quedan **documentados** con assert del comportamiento actual y comentario español `# CONCERNS.md`: `suppress_zero` con columna inexistente, valores de agrupación no-hashables, `count` truthy, y camino feliz multi-dataset.
- 3 bugs con comportamiento-correcto definido quedan como `xfail(strict=True)` que falla hoy y XPASSeará al corregirse: `detail(source=)` ignorado, totales nombrados sobre columna all-`None`, y errores chart/pivot sin contexto.
- La suite completa queda verde: `74 passed, 3 xfailed` y `ruff check` limpio.

## Task Commits

1. **Task 1: Regresiones multi-dataset y no-op/semánticas (#1, #2, #6, #8)** - `a03424e` (test) — 4 tests: `test_multi_dataset_source`, `test_suppress_zero_missing_column`, `test_detail_source_ignored`, `test_count_expression_semantics`
2. **Task 2: Regresiones de crash/error (#3, #4, #11)** - `7944a60` (test) — 3 tests: `test_named_total_none_values`, `test_unhashable_group_value`, `test_chart_pivot_error_context`

## Files Created/Modified
- `tests/test_report.py` - +95 líneas: 7 tests de regresión TEST-01 bajo dos banners nuevos (`# --- regresiones TEST-01 (multi-dataset y no-op) ---` y `# --- regresiones TEST-01 (crash/error) ---`)

## Decisions Made
- Los bugs no-corregidos se documentan (no se corrigen) para que un fix futuro sea un *cambio* detectable, no una sorpresa silenciosa — alineado con el propósito del plan.
- `TEST-01` NO se marca completo en `REQUIREMENTS.md`: la definición del requisito ("tests de regresión para cada uno de los fixes anteriores") abarca también 08-02 (renderers/seguridad, precisión, SUM/sanitización, Link/Image + smoke de rendimiento). Se marcará al cerrar 08-02.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Listo para 08-02 (regresiones renderers/seguridad + smoke de rendimiento 50k filas), que completará `TEST-01` y `TEST-02`.
- Sin blockers ni concerns nuevos.

## Self-Check: PASSED

- `tests/test_report.py` — 7 tests nuevos presentes (verificado vía `grep`).
- Commits `a03424e` (Task 1) y `7944a60` (Task 2) — presentes en el log.
- `uv run pytest -q` → `74 passed, 3 xfailed` (exit 0).
- `uv run ruff check tests/test_report.py` → exit 0.

---
*Phase: 08-tests-ci*
*Completed: 2026-09-17*
