---
phase: 08-tests-ci
plan: 02
subsystem: testing
tags: [pytest, regression-tests, security, perf-smoke, pivot, excel-formula-injection]

# Dependency graph
requires:
  - phase: 08-tests-ci (08-01)
    provides: patrón de regresión TEST-01 (assert comportamiento-actual + comentario `# CONCERNS.md`, y xfail para bugs con comportamiento-correcto definido)
  - phase: 07-refactor
    provides: traversal compartido + GroupSpec inmutable (superficie del engine bajo test)
provides:
  - 4 tests de regresión TEST-01 (renderers + seguridad) en tests/test_report_renderers.py y tests/test_security.py
  - tests/test_perf_smoke.py con smoke de rendimiento 50k filas (TEST-02, gate wall-clock < 10s)
affects: [08-tests-ci (08-03, 08-04), verifier]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Smoke test de rendimiento: gate pass/fail con `time.perf_counter()` + assert de corrección (sin pytest-benchmark ni markers)"
    - "Invariante de seguridad como test que pasa hoy (no xfail): fórmula viva solo para SUM interna generada por índices de fila"

key-files:
  created: [tests/test_perf_smoke.py]
  modified: [tests/test_report_renderers.py, tests/test_security.py]

key-decisions:
  - "Los 3 bugs no-corregidos (JSON profundo, params muertos Excel, null byte) se documentan con assert del comportamiento actual + comentario `# CONCERNS.md`, no se corrigen (alineado con la decisión de Phase 8)"
  - "TEST-01 se marca completo al cerrar 08-02 (cubre renderers + seguridad); TEST-02 NO se marca — 08-02 solo aporta 1 de 4 gates de CI (el smoke de rendimiento), el resto llega en 08-03/08-04"
  - "El invariante de no-inyección en modo fórmulas (#10) se escribe como test que pasa hoy (no xfail): es una garantía de seguridad, no un bug documentado"

patterns-established:
  - "Bug conocido (comportamiento actual): assert directo + comentario `# regresión documenta bug conocido — ver CONCERNS.md §...`"
  - "Smoke de rendimiento: asertar corrección (dimensión + total) Y wall-clock, con headroom 10× sobre lo medido"

requirements-completed: [TEST-01]

# Metrics
duration: 5min
completed: 2026-09-17
---

# Phase 08 Plan 02: Tests & CI Summary

**4 tests de regresión (renderers + seguridad) y un smoke test de rendimiento 50k filas (`tests/test_perf_smoke.py`) — cierra TEST-01 y materializa el gate de rendimiento de TEST-02**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-17T03:55:00Z
- **Completed:** 2026-09-17T04:00:00Z
- **Tasks:** 3
- **Files modified:** 3 (2 modificados + 1 nuevo)

## Accomplishments

- 2 tests de regresión de renderers: `test_deep_tree_to_json` (#5, documenta el `ValueError` de pydantic-core en árboles >1000 profundos) y `test_excel_styles_footer_dead_params` (#7, documenta que `styles`/`column_position` del footer son no-op).
- 2 tests de seguridad: `test_expression_null_byte` (#9, el null byte siempre es rechazado — `ValueError` crudo en 3.10, `ExpressionError` en 3.11+) y `test_excel_formula_mode_no_user_injection` (#10, invariante: el valor de usuario `"=1+1"` queda `data_type == "s"`, solo la `=SUM(B2)` interna es fórmula viva).
- `tests/test_perf_smoke.py` con `test_pivot_50k_rows_smoke`: aserta corrección (50×200, `row_totals[0] == 25000`) + wall-clock < 10s (elapsed real ≈ 0.26s).
- La suite completa queda verde: `79 passed, 3 xfailed` y `ruff check` limpio en los tres archivos.

## Task Commits

Each task was committed atomically:

1. **Task 1: Regresiones de renderers (#5 JSON profundo, #7 params muertos Excel)** - `dba6835` (test)
2. **Task 2: Regresiones de seguridad (#9 null byte, #10 modo fórmulas)** - `8370fe6` (test)
3. **Task 3: Smoke test de rendimiento 50k filas (TEST-02)** - `438c8f9` (test)

**Plan metadata:** *(commit docs final, ver más abajo)*

## Files Created/Modified

- `tests/test_report_renderers.py` - +35 líneas: `test_deep_tree_to_json` y `test_excel_styles_footer_dead_params` bajo banner `# --- regresiones TEST-01 (renderers) ---`
- `tests/test_security.py` - +25 líneas: `test_expression_null_byte` y `test_excel_formula_mode_no_user_injection` bajo banner `# --- regresiones TEST-01 (seguridad) ---`
- `tests/test_perf_smoke.py` - nuevo: `test_pivot_50k_rows_smoke` (corrección + wall-clock < 10s)

## Decisions Made

- Los 3 bugs sin comportamiento-correcto definido (JSON profundo, params muertos Excel, null byte) se documentan con assert del comportamiento actual + comentario `# CONCERNS.md`, no se corrigen — coherente con la decisión de Phase 8 de que un fix futuro sea un *cambio* detectable.
- `test_excel_formula_mode_no_user_injection` es un **invariante de seguridad que pasa hoy** (no un bug documentado), por lo que se escribe como assert directo sin `xfail`.
- `TEST-01` se marca completo (08-01 + 08-02 cubren idempotencia, precisión, SUM, sanitización, `order_by`, errores con contexto, multi-dataset, Link/Image y jerarquías profundas). `TEST-02` NO se marca completo: 08-02 solo aporta el gate de smoke de rendimiento (1 de 4 gates de CI); type checker, `ruff format --check` y cobertura llegan en 08-03/08-04.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Listo para 08-03 (tooling config: mypy + pytest-cov + secciones `[tool.*]` + normalización one-time de `ruff format`).
- Sin blockers ni concerns nuevos. `TEST-02` queda abierto para completarse en 08-03/08-04.

---

## Self-Check: PASSED

- `tests/test_perf_smoke.py` — presente (verificado vía `[ -f ]`).
- `.planning/phases/08-tests-ci/08-02-SUMMARY.md` — presente.
- Commits `dba6835` (Task 1), `8370fe6` (Task 2), `438c8f9` (Task 3) — presentes en el log.
- `uv run pytest -q` → `79 passed, 3 xfailed` (exit 0).
- `uv run ruff check tests/test_report_renderers.py tests/test_security.py tests/test_perf_smoke.py` → exit 0.

---

*Phase: 08-tests-ci*
*Completed: 2026-09-17*
