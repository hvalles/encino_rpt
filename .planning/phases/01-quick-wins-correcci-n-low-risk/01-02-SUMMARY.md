---
phase: 01-quick-wins-correcci-n-low-risk
plan: 02
subsystem: api
tags: [order_by, aggregation, custom-functions, expression-evaluator, error-handling, values]

# Dependency graph
requires:
  - phase: 01-quick-wins-correcci-n-low-risk
    provides: "baseline 41-test suite and phase-C ordering call site (_apply_order at aggregation.py:260) as analyzed in 01-RESEARCH/01-PATTERNS"
provides:
  - "order_by(expression=...) evaluates with report._functions (add_function custom functions) — CORR-04/D-04"
  - "order_by(total=...) with a missing total raises ValueError naming the total and child instead of raw TypeError — CORR-05/D-05/D-06"
affects: [01-03-deps, phase-3-robustness, phase-8-regression-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Function threading: _apply_order/_sort_key now receive functions and pass report._functions to evaluate (pattern aligned with aggregation.py:102,174,365,396)"
    - "Ruidoso raise (no fallback) en rama total de _sort_key: ValueError en español con !r + contexto del hijo, propagado por sorted() en el primer hijo faltante (D-05/D-06)"

key-files:
  created: []
  modified:
    - encino_rpt/aggregation.py
    - tests/test_report.py

key-decisions:
  - "D-04: _sort_key branch expression pasa report._functions (era {}); NO se inyecta TOTAL() en el contexto de orden"
  - "D-05/D-06: total ausente en order_by(total=...) lanza ValueError f\"total de orden inexistente: {total!r} (hijo {child_desc!r})\" en _sort_key — raise en el primer hijo evaluado por sorted(), sin pre-validación ni fallback"

patterns-established:
  - "Pattern 1 (RESEARCH): threading de funciones del reporte — el único sitio divergente ({}) queda alineado con los 4 sitios canónicos"
  - "Pattern 2 (RESEARCH): errores en español con !r + contexto — convención aggregation.py:45 aplicada a la rama total de _sort_key"

requirements-completed: [CORR-04, CORR-05]

# Metrics
duration: 6min
completed: 2026-09-17
---

# Phase 1 Plan 2: order_by custom-function evaluation + missing-total error Summary

**`order_by(expression=...)` now evaluates against the report's registered custom functions (`report._functions` threaded through `_apply_order`/`_sort_key` — `add_function("doblado", ...)` sorts without `ExpressionError`), and `order_by(total=...)` with a never-declared total now raises a Spanish `ValueError` naming the total and child (`total de orden inexistente: 'total_inexistente' (hijo 'por_agente')`) instead of a raw `TypeError` from `sorted()` (CORR-04/CORR-05, D-04/D-05/D-06) — guarded by 2 new regression tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-09-17T00:53:00Z (approx.)
- **Completed:** 2026-09-17T00:58:27Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- CORR-04 (D-04): `_sort_key` was the only evaluation site passing `{}` as the functions context (aggregation.py:300). Threaded `report._functions` through `_apply_order`/`_sort_key` and the single call site (`aggregation.py:260`), aligning with the 4 canonical threading sites (102, 174, 365, 396). `order_by(expression="doblado(total)", direction="desc")` with `add_function("doblado", lambda v: v * 2)` now sorts `["Bob", "Cid", "Ana"]` (600/400/200). `TOTAL()` is NOT injected into the ordering context (locked D-04).
- CORR-05 (D-05/D-06): the `total` branch of `_sort_key` returned `None` on a missing total, letting `sorted()` fail with a raw `TypeError: '<' not supported ...`. Replaced with `raise ValueError(f"total de orden inexistente: {total!r} (hijo {child_desc!r})")`. Because the raise lives inside `sorted()`'s key function, it fires on the first child lacking the total during `run()` (D-06) — no pre-validation, no silent fallback (project convention: raise, not silence).
- Verified error message exactly matches the plan's success criteria: `ValueError: total de orden inexistente: 'total_inexistente' (hijo 'por_agente')`.
- 2 new regression tests in `tests/test_report.py`: `test_order_by_expression_with_custom_function` and `test_order_by_missing_total_raises`. Full suite: 43 passed (was 41); `ruff check` clean. Both tests were proven RED against the current code first (ExpressionError `'doblado'` / raw TypeError).

## Task Commits

Each task was committed atomically:

1. **Task 1: RED regression tests (CORR-04 + CORR-05)** - `0514241` (test)
2. **Task 2: function threading + missing-total raise in order_by** - `83698ad` (feat)

**Plan metadata:** `docs(01-02): add plan summary` (this commit, created after per-task commits)

## Files Created/Modified

- `encino_rpt/aggregation.py` - `_apply_order(spec, children, functions)` / `_sort_key(child, ob, functions)` signatures; `sorted()` key now `_sort_key(c, ob, functions)`; total branch raises `ValueError` (child_desc from `child.name` or `child.key`); expression branch evaluates with `functions`; call site passes `report._functions`. `_is_zero`, `suppress_zero`, `top_n`, the `column` branch, and `return 0` untouched; `Section.order_by`/`GroupSpec.order_by` untouched.
- `tests/test_report.py` - two tests appended after `test_order_top_suppress`: custom-function expression ordering (Bob/Cid/Ana) and `pytest.raises(ValueError, match="total de orden inexistente: 'total_inexistente'")` on `rep.run()`. Existing 16 tests untouched.

## Decisions Made

- Implemented locked decisions D-04, D-05, D-06 exactly as specified in CONTEXT/RESEARCH/PATTERNS (verified replacement code used verbatim, Research §Code Examples 3).
- `child_desc` prefers `child.name` (group name, e.g. `'por_agente'`) falling back to `child.key` — gives the child context the plan's success criteria expects (`(hijo 'por_agente')`).

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed
**Impact on plan:** N/A — no unplanned work required.

## Issues Encountered

None. RED phase proved both bugs (ExpressionError `'doblado'` on expression ordering; raw `TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'` on missing total); GREEN phase passed on first run (2/2 `-k "order_by"`, 18/18 full file).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for plan `01-03` (DEP-01: remove `encino-orm` + docs cleanup); the aggregation pipeline is now consistent across all 5 evaluation sites.
- Threat register: T-01-04 (Tampering, expression branch) and T-01-05 (DoS, sorted key raise) both disposition `accept` per plan — the ordering context receives only `report._functions` (author-controlled), the AST whitelist and `_MAX_*` guards are untouched, and the ValueError propagates through `run()` per project convention. No new attack surface introduced (no new endpoints/files/schema).

## Self-Check: PASSED

- `encino_rpt/aggregation.py` and `tests/test_report.py` exist and contain the planned changes (verified via `git diff a5f6888`).
- Commits `0514241` (test RED) and `83698ad` (feat GREEN) verified in `git log`; TDD gate order (test → feat) satisfied.
- Full verification: `uv run pytest -q` → 43 passed (0.32s); `uv run ruff check` → All checks passed; combined exit 0, well under the 60s budget.

---
*Phase: 01-quick-wins-correcci-n-low-risk*
*Completed: 2026-09-17*