---
phase: 08-tests-ci
plan: 03
subsystem: testing
tags: [mypy, pytest-cov, coverage, ruff, pyproject, tooling]

# Dependency graph
requires:
  - phase: 08-02
    provides: "regresión renderers/seguridad + smoke 50k filas (TEST-01 + TEST-02 perf)"
provides:
  - "mypy 2.3.1 + pytest-cov 7.1.0 en el grupo dev y bloqueados en uv.lock"
  - "secciones [tool.mypy], [tool.ruff], [tool.ruff.format], [tool.coverage.run], [tool.coverage.report]"
  - "normalización one-time de ruff format sobre encino_rpt/ y tests/ (scoped, sin .md)"
affects: [08-04]

# Tech tracking
tech-stack:
  added: [mypy 2.3.1, pytest-cov 7.1.0, coverage 7.16.1]
  patterns: ["config [tool.*] en pyproject.toml", "ruff format scoped a encino_rpt tests (extend-exclude protege .planning/ y docs/)"]

key-files:
  created: []
  modified: [pyproject.toml, uv.lock, encino_rpt/ (16 .py), tests/ (4 .py)]

key-decisions:
  - "mypy 2.3.1 (no 1.x): RESEARCH.md Pitfall 4 verificó que el plugin pydantic.mypy carga sin error"
  - "ruff format scoped a `encino_rpt tests` (nunca `.`), inmune a los 17 `.md` de `.planning/` y `docs/`"

patterns-established:
  - "Config de tools en pyproject.toml: [tool.mypy] con plugin pydantic.mypy (sin --strict); [tool.ruff] sin select/ignore (conserva lint default); [tool.coverage.report] fail_under=80"
  - "Normalización one-time antes del gate de CI (anti-Pitfall #1): el formato se normaliza y se verifica `--check` scoped"

requirements-completed: []  # TEST-02 NO completo aquí — los jobs de CI (type check en CI, format gate, coverage gate) aterrizan en 08-04

# Metrics
duration: 4min
completed: 2026-09-17
---

# Phase 8 Plan 03: Tooling config + normalización one-time de ruff format

**mypy + pytest-cov como dev-deps con 5 secciones `[tool.*]` en pyproject.toml y normalización scoped de ruff format sobre `encino_rpt/` y `tests/`**

## Performance

- **Duration:** 4 min
- **Started:** 2026-09-17T04:01:41Z
- **Completed:** 2026-09-17T04:03:54Z
- **Tasks:** 2
- **Files modified:** 22 (pyproject.toml + uv.lock + 20 archivos `.py`)

## Accomplishments

- `mypy>=2.3.1` y `pytest-cov>=7.1.0` añadidos al grupo `dev` (coverage.py 7.16.1 entra transitivamente); `uv.lock` actualizado con las 3 entradas (`mypy`, `pytest-cov`, `coverage`).
- 5 secciones TOML nuevas en `pyproject.toml`: `[tool.mypy]` (plugin `pydantic.mypy`, `python_version=3.10`, sin `--strict`), `[tool.ruff]` (`target-version=py310`, `line-length=88`, `extend-exclude=[".planning", "docs", "dist", "build", ".venv"]`), `[tool.ruff.format]` (`quote-style="double"`), `[tool.coverage.run]` (`source=["encino_rpt"]`), `[tool.coverage.report]` (`fail_under=80`, `show_missing`, `exclude_lines`).
- Invariante preservada: `[project] dependencies` sigue siendo únicamente `["pydantic>=2"]` (pydantic es la única dep de runtime).
- Normalización one-time `uv run ruff format encino_rpt tests` — 20 archivos reformateados (solo whitespace/comillas, sin cambios de lógica), ningún `.md` tocado.
- Gates verdes: `ruff format --check encino_rpt tests` (24 files already formatted), `ruff check` (All checks passed), `pytest -q` (79 passed, 3 xfailed).

## Task Commits

Cada tarea fue commiteada atómicamente:

1. **Task 1: Añadir deps (mypy, pytest-cov) + secciones de config** - `f92069c` (chore)
2. **Task 2: Normalización one-time de ruff format (scoped)** - `4b76ae3` (style)

## Files Created/Modified

- `pyproject.toml` - mypy+pytest-cov en grupo `dev`; 5 secciones `[tool.*]` nuevas tras `[dependency-groups]`
- `uv.lock` - bloquea mypy 2.3.1, pytest-cov 7.1.0, coverage 7.16.1 (+ transitivas)
- `encino_rpt/` (16 archivos `.py`) - reformateados (ruff format, solo formato)
- `tests/` (4 archivos `.py`) - reformateados (ruff format, solo formato)

## Decisions Made

- **mypy 2.3.1 en lugar de 1.x** — `uv run mypy --version` confirma `mypy 2.3.1` y el plugin `pydantic.mypy` carga sin error (contingencia Pitfall 4 de RESEARCH.md no necesaria).
- **`ruff format` scoped a `encino_rpt tests`** (no `.`) — evita reformatear los 17 `.md` de `.planning/` y `docs/`; el `extend-exclude` en `[tool.ruff]` es defensa adicional para el gate de CI.
- **TEST-02 NO se marca completo** — este plan aporta solo tooling + normalización; los jobs de CI (type check, `ruff format --check` en CI, gate de cobertura) aterrizan en 08-04.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Tooling listo para 08-04: `[tool.mypy]`, `[tool.ruff]`, `[tool.ruff.format]`, `[tool.coverage.*]` presentes; `ruff format --check encino_rpt tests` ya verde.
- 08-04 pendiente: reestructurar `.github/workflows/ci.yml` en jobs `test` + `quality` (mypy + ruff format --check + pytest --cov-fail-under=80), triage de `uv run mypy encino_rpt` y verificación end-to-end de gates.

---

## Self-Check: PASSED

- `pyproject.toml` (5 secciones `[tool.*]`), `uv.lock` (mypy/pytest-cov/coverage), 20 `.py` reformateados — verificados.
- Commits `f92069c`, `4b76ae3` presentes en `git log`.
- Suite verde: `uv run pytest -q` → 79 passed, 3 xfailed.

---
*Phase: 08-tests-ci*
*Completed: 2026-09-17*
