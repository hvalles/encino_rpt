---
phase: 08-tests-ci
plan: 04
subsystem: ci
tags: [mypy, ci, coverage, ruff, quality-gates, type-check]

# Dependency graph
requires:
  - phase: 08-03
    provides: "mypy 2.3.1 + pytest-cov en grupo dev; secciones [tool.mypy]/[tool.ruff]/[tool.coverage.*]; normalización ruff format"
provides:
  - "uv run mypy encino_rpt limpio (exit 0, 20 source files sin errores)"
  - "ci.yml con jobs test (matrix 3.10-3.13) + quality (singleton 3.13: mypy + ruff format --check + coverage)"
  - "los 5 gates de CI verificados end-to-end localmente (pytest, ruff check, mypy, format, coverage 84%)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "disable_error_code=[import-untyped] para deps opcionales sin stubs (openpyxl/reportlab)"
    - "alias Child = Detail | Group | Chart | Pivot para tipar la unión recursiva de Group.children"
    - "job quality singleton (3.13) sin needs, paralelo al job test (matrix)"

key-files:
  created: []
  modified:
    - encino_rpt/aggregation.py
    - encino_rpt/expressions.py
    - encino_rpt/pivot.py
    - encino_rpt/renderers/pdf.py
    - encino_rpt/renderers/excel.py
    - pyproject.toml
    - .github/workflows/ci.yml

key-decisions:
  - "mypy 2.3.1 confirmado (contingencia 1.20.2 NO necesaria): el plugin pydantic.mypy carga y el triage completa sin pinar 1.x"
  - "disable_error_code=[import-untyped] en lugar de # type: ignore[import-untyped] por línea: evita fricción con ruff isort (I001) en imports multilinea y es el relax justificado que el plan permite"
  - "quality job sin needs (paralelo a test), replicando el patrón multi-job de publish.yml/docs.yml"

requirements-completed: [TEST-02]

# Metrics
duration: 11min
completed: 2026-09-17
---

# Phase 8 Plan 04: CI endurecido (mypy limpio + jobs test/quality) y verificación end-to-end

**`uv run mypy encino_rpt` sale limpio (triage de 25 errores), ci.yml se reestructura en jobs `test` + `quality`, y los 5 gates de CI se verifican localmente (coverage 84%).**

## Performance

- **Duration:** 11 min
- **Started:** 2026-09-17T04:05Z
- **Completed:** 2026-09-17T04:16Z
- **Tasks:** 3
- **Files modified:** 7 (6 archivos `.py` + `pyproject.toml` + `ci.yml`)

## Accomplishments

- **TEST-02 completo**: `uv run mypy encino_rpt` → `Success: no issues found in 20 source files` (exit 0). Los 25 errores iniciales se triagaron así:
  - **8 × `import-untyped`** (openpyxl/reportlab, deps opcionales sin stubs) → `disable_error_code = ["import-untyped"]` en `[tool.mypy]` (relax justificado, no `# type: ignore` por línea para evitar fricción con ruff I001).
  - **11 × `var-annotated`** → anotaciones concretas (`cum: dict[str, Any]`, `children_map: dict[str, list[GroupSpec]]`, `buckets`, `rows`/`spans`, `group_stack`, `registry`/`deferred`, etc.).
  - **2 × expressions.py** → tipar `_UNARY: dict[type[ast.unaryop], Callable[[Any], Any]]` y renombrar `op`→`uop` (clash de tipos binario/unario).
  - **4 × aggregation.py** (lista polimórfica `children`) → alias `Child = Detail | Group | Chart | Pivot` para `children` y `extras`.
- **ci.yml reestructurado**: job `test` (matrix 3.10–3.13, `uv run pytest` + `uv run ruff check`) intacto; job `quality` nuevo (singleton 3.13) con `mypy`, `ruff format --check encino_rpt tests` y `pytest --cov-fail-under=80`.
- **Verificación end-to-end (los 5 gates pasan localmente):**
  1. `uv run pytest -q` → **79 passed, 3 xfailed** (exit 0)
  2. `uv run ruff check` → **All checks passed** (exit 0)
  3. `uv run mypy encino_rpt` → **Success: no issues found** (exit 0)
  4. `uv run ruff format --check encino_rpt tests` → **24 files already formatted** (exit 0)
  5. `uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80` → **TOTAL 84%** (83.87%), ≥80% (exit 0)

## Task Commits

1. **Task 1: Triage de mypy hasta exit 0** - `2c8500d` (refactor)
2. **Task 2: Reestructurar ci.yml en jobs test + quality** - `92e4a40` (chore)
3. **Task 3: Verificación end-to-end de los gates** - sin commit (verificación pura; no produjo cambios de archivos)

## Files Created/Modified

- `encino_rpt/aggregation.py` - alias `Child`, anotaciones de `cum`/`children_map`/`index`/`registry`/`deferred`/`children`/`extras`
- `encino_rpt/expressions.py` - `_UNARY` tipado + renombrar `op`→`uop`
- `encino_rpt/pivot.py` - anotar `buckets`/`row_buckets`/`col_buckets`
- `encino_rpt/renderers/pdf.py` - anotar `rows`/`spans`
- `encino_rpt/renderers/excel.py` - anotar `group_stack`
- `pyproject.toml` - `[tool.mypy] disable_error_code = ["import-untyped"]`
- `.github/workflows/ci.yml` - job `quality` (singleton 3.13) añadido junto a `test`

## Decisions Made

- **mypy 2.3.1 en lugar de 1.20.2** — el plugin `pydantic.mypy` carga sin error (contingencia Pitfall 4 de RESEARCH.md NO necesaria); el triage se resolvió íntegramente con mypy 2.3.1.
- **`disable_error_code = ["import-untyped"]` en vez de 8 × `# type: ignore[import-untyped]`** — el `# type: ignore` en imports multilinea choca con ruff isort (I001), y el `disable_error_code` es el relax "justificado" que la acceptance criteria del plan permite explícitamente para deps opcionales sin stubs.
- **`quality` sin `needs`** — corre en paralelo con `test` (independiente de la matrix), replicando el patrón multi-job de `publish.yml`/`docs.yml`.

## Deviations from Plan

Ninguna estructural. Ajuste de triage documentado (no Rule 4):

**1. [Triaging - import-untyped vía config en lugar de `# type: ignore` por línea]**
- **Encontrado en:** Task 1
- **Asunto:** El plan prefiere (b) `# type: ignore[code]` sobre (c) `disable_error_code`, pero el `# type: ignore[import-untyped]` en imports de `reportlab`/`openpyxl` dispara `I001` de ruff (reorganización de imports) que exigiría romper el import y mover el comentario, arriesgando que mypy deje de verlo.
- **Fix:** `disable_error_code = ["import-untyped"]` en `[tool.mypy]` — relax global mínimo, honesto ("deps opcionales sin stubs"), y explícitamente permitido por la acceptance criteria de Task 1.
- **Archivos modificados:** `pyproject.toml`
- **Commit:** `2c8500d`

## Issues Encountered

- Primer intento con `# type: ignore[import-untyped]` produjo `I001` (ruff isort) en `pdf.py` → resuelto cambiando a `disable_error_code` (ver Deviations).

## User Setup Required

Ninguno — la ejecución real de GitHub Actions en push es la única verificación manual pendiente (VALIDATION.md §Manual-Only); no requiere acción del usuario en este plan.

## Next Phase Readiness

- Fase 08 completa: TEST-01 (tests de regresión, 08-01/08-02) y TEST-02 (smoke perf 08-02 + tooling/normalización 08-03 + mypy/CI/coverage 08-04) cerrados.
- Los 4 checks singleton (mypy, format, coverage) corren una sola vez en Python 3.13; el smoke de rendimiento se queda en `pytest` para toda la matrix.

---

## Self-Check: PASSED

- `uv run mypy encino_rpt` → exit 0 (20 source files, sin errores).
- Commits `2c8500d` y `92e4a40` presentes en `git log`.
- `grep -c "uv run mypy encino_rpt" ci.yml` == 1, `ruff format --check` == 1, `cov-fail-under=80` == 1; jobs `test:` y `quality:` 1 coincidencia cada uno.
- Gates: pytest 79 passed, ruff check limpio, mypy limpio, format 24 files, coverage 84% (≥80).

---
*Phase: 08-tests-ci*
*Completed: 2026-09-17*
