---
phase: 01-quick-wins-correcci-n-low-risk
plan: 01
subsystem: ui
tags: [format_value, sanitizer, csv-injection, cwe-1236, excel, decimal, utf-8-bom]

# Dependency graph
requires: []
provides:
  - "format_value full precision with decimals=None (str() round-trip repr + Decimal percent scale) — CORR-02"
  - "is_dangerous whitespace/BOM-trimmed prefix detection closing the CSV/Excel formula-injection bypass — SEC-02"
affects: [01-02-order-by, 01-03-deps, phase-2-excel-sanitization, phase-3-robustness]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "str(abs(value)) round-trip repr en branch decimals=None (D-01/D-02)"
    - "Escala percent exacta via Decimal(str(abs(value))) * 100 + normalize() + format(d, 'f') (D-03)"
    - "Recorte ^[\\s\\ufeff]+ antes del chequeo de prefijos en is_dangerous, fuente única CSV+Excel (D-07/D-08)"

key-files:
  created: []
  modified:
    - encino_rpt/renderers/_format.py
    - encino_rpt/renderers/_sanitize.py
    - tests/test_report_renderers.py
    - tests/test_security.py
    - docs/security.md

key-decisions:
  - "D-01/D-02: decimals=None usa str() (repr round-trip corto); sci solo en |num|>=1e16 o <1e-4 (umbrales nativos de CPython)"
  - "D-03: percent_scale con decimals=None escala via Decimal para evitar el artefacto binario 7.000000000000001"
  - "D-07/D-08: is_dangerous recorta ^[\\s\\ufeff]+ antes de chequear prefijos; cubre CSV y Excel sin tocar consumidores"
  - "D-09: sanitize_csv prefija ' al valor ORIGINAL verbatim (\" =1+1\" → \"' =1+1\") — sin cambios en sanitize_csv"
  - "neg = num < 0 se calcula antes de las ramas (signo invariante ante escala ×100 para valores finitos)"

patterns-established:
  - "Pattern 3 (RESEARCH): formato de precisión con escala Decimal"
  - "Pattern 4 (RESEARCH): fuente única de verdad del sanitizer (is_dangerous ampliado, consumidores intactos)"

requirements-completed: [CORR-02, SEC-02]

# Metrics
duration: 12min
completed: 2026-09-16
---

# Phase 1 Plan 1: format_value full precision + formula-injection sanitizer hardening Summary

**`format_value` now renders full precision with `decimals=None` (`"1234567.89"`, never `"1.23457e+06"`) via `str()` round-trip repr with exact Decimal percent scaling, and `is_dangerous` now trims leading whitespace/BOM (`^[\s\ufeff]+`) before prefix checks, closing the CWE-1236 CSV/Excel injection bypass (D-01/D-02/D-03/D-07/D-08/D-09) — all guarded by 9 new regression tests**

## Performance

- **Duration:** 12 min
- **Started:** 2026-09-17T00:43:00Z (approx.)
- **Completed:** 2026-09-17T00:55:51Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- CORR-02: `format_value` branch `decimals=None` uses `str(abs(value))` (repr round-trip, D-01); scientific notation only at CPython-native extremes `|num|>=1e16` / `<1e-4` (D-02); `percent_scale` with `decimals=None` scales via `Decimal(str(abs(value))) * 100).normalize()` + `format(d, "f")` producing clean `"7%"`/`"29%"`/`"25.6%"` (D-03).
- SEC-02: `is_dangerous` trims `^[\s\ufeff]+` before the `_DANGEROUS_PREFIXES` check (D-07); single shared source fixes both CSV and Excel without touching `sanitize_csv`/`write_excel_cell` (D-08); `sanitize_csv` still prefixes the ORIGINAL value verbatim (D-09, e.g. `"' =1+1"`).
- docs/security.md updated: sanitizer section now describes post-trim detection (`espacios en blanco y BOM (\ufeff)`) and the shared single source for both formats.
- 9 new regression tests: 6 precision tests in `tests/test_report_renderers.py` + 3 P5 tests in `tests/test_security.py`. Full suite: 41 passed (was 32); `ruff check` clean.

## Task Commits

Each task was committed atomically:

1. **Task 1: RED regression tests (CORR-02 + SEC-02)** - `98fbc19` (test)
2. **Task 2: format_value full precision (CORR-02)** - `781b1ef` (feat)
3. **Task 3: is_dangerous whitespace/BOM trim (SEC-02) + docs** - `a2447a3` (feat)

**Plan metadata:** `docs(01-01): add plan summary` (this commit, created after per-task commits)

## Files Created/Modified

- `encino_rpt/renderers/_format.py` - `format_value` numeric branch: `decimals=None` → `str(abs(value))`; `elif fmt.percent_scale` → Decimal scale; downstream (thousands/percent/symbol/negative) untouched; `_add_thousands`/`excel_number_format` untouched
- `encino_rpt/renderers/_sanitize.py` - added `import re`, `_LEADING_TRIM = re.compile(r"^[\s\ufeff]+")`, new `is_dangerous` body + docstring; `_DANGEROUS_PREFIXES`/`sanitize_csv`/`write_excel_cell` untouched
- `tests/test_report_renderers.py` - 6 new `test_format_value_precision_*` tests (no_sci, thousands, percent_scale, sci_extremes, whole_float, currency); existing tests untouched
- `tests/test_security.py` - new import of `is_dangerous`/`sanitize_csv`, P5 banner block with 3 tests (is_dangerous, sanitize_csv, excel); P1-P4 untouched
- `docs/security.md` - sanitizer section describes post-trim detection and shared single source

## Decisions Made

- Implemented locked decisions D-01, D-02, D-03, D-07, D-08, D-09 exactly as specified in CONTEXT/RESEARCH/PATTERNS (verified replacement code used verbatim).
- `neg = num < 0` is computed before the three branches (on the pre-scaled `num`); the sign is invariant under ×100 scaling for finite values, preserving the original semantics for the decimals path.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed
**Impact on plan:** N/A — no unplanned work required.

## Issues Encountered

None. RED phase proved both bugs (sci `'1.23457e+06'` and `is_dangerous(' =1+1') == False`); GREEN phase passed on first run for both files.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Ready for plan `01-02` (order_by with custom functions CORR-04 + missing-total error CORR-05); the sanitizer single-source pattern (D-08) is in place for any Excel-wide sanitization review in Phase 2.
- Threat register entries T-01-01 (CSV) and T-01-02 (Excel) are mitigated; T-01-03 (prefix list) accepted as pre-existing behavior; T-01-SC (deps) N/A — no packages installed this plan.

## Self-Check: PASSED

- `encino_rpt/renderers/_format.py`, `encino_rpt/renderers/_sanitize.py`, both test files, `docs/security.md` exist and contain the planned changes.
- Commits `98fbc19`, `781b1ef`, `a2447a3` verified in `git log`.
- Full verification: `uv run pytest -q` → 41 passed; `uv run ruff check` → All checks passed; touched test files run in 0.33s (< 60s).

---
*Phase: 01-quick-wins-correcci-n-low-risk*
*Completed: 2026-09-16*