---
phase: 09-readers-multi-formato
plan: 01
subsystem: api
tags: [python, pydantic, readers, csv, json, openpyxl, coercion]

# Dependency graph
requires:
  - phase: 08-tests-ci
    provides: [ruff/mypy/pytest tooling, test conventions]
provides:
  - "encino_rpt/readers.py: protocolo Reader + registro + readers stdlib + excel + _coerce"
  - "Report.read / Report.register_reader (classmethods)"
  - "tests/test_readers.py (12 tests)"
affects: [10-templates-html-markdown, future readers custom, docs]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Reader Protocol (typing.Protocol) + registro módulo-level register_reader/get_reader"
    - "import perezoso de openpyxl dentro de ExcelReader.read (mismo patrón que renderers/excel.py)"
    - "_coerce: auto-detección determinista null→bool→int→float→str"

key-files:
  created: [encino_rpt/readers.py, tests/test_readers.py]
  modified: [encino_rpt/report.py, encino_rpt/__init__.py]

key-decisions:
  - "Reader como Protocol (typing.Protocol), no ABC: no obliga a heredar; cualquier objeto con read(source, **opts) vale"
  - "coerce solo aplica a texto delimitado (csv/tsv); json/jsonl/tuples/excel preservan tipos ya tipados (evita corromper IDs tipo '001' -> 1)"
  - "json/jsonl lanzan TypeError (no ValueError) para desajuste de tipo, alineado con ruff TRY004"

patterns-established:
  - "Reader multi-formato: ruta (str/PathLike) | file-like (.read()) | datos crudos, normalizado con _read_text/_read_text_auto"
  - "Resolución de formato por extensión (.csv/.tsv/.json/.jsonl/.xlsx/.xlsm)"

requirements-completed: [READ-01, READ-02, READ-03, READ-04, READ-05]

# Metrics
duration: 5min
completed: 2026-09-17
---

# Phase 9 Plan 1: Readers multi-formato Summary

**Entrada multi-formato a `Report` vía `encino_rpt/readers.py`: protocolo `Reader`, registro de readers (built-in + custom) y auto-detección de tipos determinista.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-09-17T05:28:19Z
- **Completed:** 2026-09-17T05:32:48Z
- **Tasks:** 3
- **Files modified:** 4 (2 creados, 2 modificados)

## Accomplishments

- `encino_rpt/readers.py` con protocolo `Reader`, `register_reader`/`get_reader`, `_coerce` y readers incorporados `csv`, `tsv`, `json`, `jsonl`, `tuples` y `excel` (lazy openpyxl).
- `Report.read(...)` y `Report.register_reader(...)` como classmethods que delegan en el módulo readers; `Reader` exportado en `__all__`.
- `_coerce` auto-detecta por celda en orden `null → bool → int → float → str` con opt-out `coerce=False`.
- `tests/test_readers.py` con 12 tests (CSV/TSV/JSON/JSONL/tuplas/custom/excel + auto-detección + regresión `Report(rows=...)`).
- Suite completa verde: `93 passed, 3 xfailed`; `ruff check`, `mypy`, y `ruff format --check` limpios.

## Task Commits

Each task was committed atomically:

1. **Task 1: módulo readers (Reader/registro/_coerce/readers stdlib + excel)** - `888a795` (feat)
2. **Task 2: Report.read/register_reader + export Reader** - `a95531c` (feat)
3. **Task 3: tests/test_readers.py** - `1c77dbb` (test)

**Plan metadata:** `(final)` (docs: complete plan)

## Files Created/Modified

- `encino_rpt/readers.py` - Protocolo `Reader`, registro, `_coerce`, readers stdlib (`csv`/`tsv`/`json`/`jsonl`/`tuples`) y `excel` (lazy), `read()` con resolución por extensión.
- `encino_rpt/report.py` - classmethods `Report.read` y `Report.register_reader`.
- `encino_rpt/__init__.py` - exporta `Reader` y lo añade a `__all__`.
- `tests/test_readers.py` - 12 tests de readers y auto-detección.

## Decisions Made

- `Reader` como `typing.Protocol` (no ABC): no fuerza herencia; cualquier objeto con `read(source, **opts) -> list[dict]` es un reader válido.
- `coerce` solo aplica a texto delimitado (csv/tsv); json/jsonl/tuples/excel preservan los tipos ya tipados — evita que un ID `"001"` en JSON se convierta en `1` (pérdida de ceros a la izquierda).
- Excepciones de desajuste de tipo en json/jsonl como `TypeError` (ruff TRY004), no `ValueError`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Aclaración] Ejemplo de aceptación de `tuples` inconsistente en el plan**
- **Found during:** Task 1
- **Issue:** El plan ilustraba `read([("x",1)], format="tuples", columns=["c"])` → `[{"c":1}]`, pero la especificación canónica (`dict(zip(columns, row))`) empareja una tupla de 2 campos con 1 columna, produciendo `{"c": "x"}`. El ejemplo era internamente inconsistente.
- **Fix:** Seguí la especificación autoritativa (`dict(zip(columns, row))`); los tests usan longitudes coincidentes.
- **Files modified:** encino_rpt/readers.py, tests/test_readers.py
- **Verification:** `read([("Ana", 100), ("Bob", 50)], format="tuples", columns=["n", "m"])` → `[{"n":"Ana","m":100},{"n":"Bob","m":50}]`.

**2. [Rule 1 - Bug] ruff TRY004: excepción de tipo en json/jsonl**
- **Found during:** Task 1
- **Issue:** `raise ValueError(...)` para validar `isinstance` disparaba `TRY004 Prefer TypeError exception for invalid type` en ruff.
- **Fix:** Cambiado a `TypeError` para los desajustes de tipo en `json`/`jsonl`.
- **Files modified:** encino_rpt/readers.py
- **Verification:** `uv run ruff check encino_rpt` limpio.

---

**Total deviations:** 2 (1 aclaración de especificación, 1 auto-fix ruff)
**Impact on plan:** Ningún cambio de alcance; el comportamiento sigue la especificación canónica del plan.

## Issues Encountered

- Ninguna de bloqueo. `openpyxl` ya está instalado en el dev env (3.1.5), así que el reader `excel` se prueba positivamente y el caso `ImportError` se cubre con `monkeypatch.setitem(sys.modules, "openpyxl", None)`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Readers multi-formato listos; `Report.read`/`Report.register_reader` disponibles para Phase 10 (Templates HTML + Markdown).
- Sin blockers; el workflow de Docs de GitHub Pages sigue como preocupación preexistente (ajena a esta fase).

---
*Phase: 09-readers-multi-formato*
*Completed: 2026-09-17*

## Self-Check: PASSED

- Created files exist: `encino_rpt/readers.py`, `tests/test_readers.py` ✓
- Modified files exist: `encino_rpt/report.py`, `encino_rpt/__init__.py` ✓
- Commits exist: `888a795`, `a95531c`, `1c77dbb` ✓
