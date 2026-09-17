---
phase: 01
slug: quick-wins-correcci-n-low-risk
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-09-16
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths=["tests"]`, `pythonpath=["."]` |
| **Quick run command** | `uv run pytest -q` |
| **Full suite command** | `uv run pytest && uv run ruff check` |
| **Estimated runtime** | ~1 s suite + ~2 s ruff |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

> Estructura final: 3 planes / 7 tasks. Onda 1 = 01-01 + 01-02 (sin solapamiento de archivos); onda 2 = 01-03 (depende de 01-01/01-02: la suite completa tras `uv sync` incluye las regresiones nuevas).
> Los comandos de la columna *Automated Command* son los `<verify><automated>` de cada plan.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01-01 | 1 | CORR-02, SEC-02 | — | N/A (tests RED que deben fallar contra el código actual) | unit (RED) | `uv run pytest tests/test_report_renderers.py -k "precision" -x; test $? -ne 0`; `uv run pytest tests/test_security.py -k "leading_space_bom" -x; test $? -ne 0` | ❌ test_add | ⬜ pending |
| 01-01-02 | 01-01 | 1 | CORR-02 | — | N/A | unit | `uv run pytest tests/test_report_renderers.py -x` | ✅ tests de 01-01-01 | ⬜ pending |
| 01-01-03 | 01-01 | 1 | SEC-02 | T-01-01, T-01-02 | `is_dangerous` post-recorte whitespace/BOM (D-07); fuente única compartida CSV+Excel (D-08); CSV prefijo `'` sobre valor ORIGINAL (D-09); Excel `data_type='s'` | unit | `uv run pytest tests/test_security.py -x` | ✅ tests de 01-01-01 | ⬜ pending |
| 01-02-01 | 01-02 | 1 | CORR-04, CORR-05 | — | N/A (tests RED que deben fallar contra el código actual) | unit (RED) | `uv run pytest tests/test_report.py -k "order_by" -x; test $? -ne 0` | ❌ test_add | ⬜ pending |
| 01-02-02 | 01-02 | 1 | CORR-04, CORR-05 | T-01-04, T-01-05 | Contexto de orden SOLO `report._functions` (D-04, accept); `raise ValueError` con `!r` que nombra el total + hijo (D-05/D-06, accept) | unit | `uv run pytest tests/test_report.py -x` | ✅ tests de 01-02-01 | ⬜ pending |
| 01-03-01 | 01-03 | 2 | DEP-01 | T-01-06, T-01-07 | Superficie de ataque de la cadena de suministro reducida: 6 paquetes podados del árbol de dependencias (mitigate) | smoke | `grep -n "encino-orm" pyproject.toml uv.lock; test $? -eq 1`; `uv run pytest -q` | ✅ pyproject.toml / uv.lock | ⬜ pending |
| 01-03-02 | 01-03 | 2 | DEP-01 | T-01-08 | Docs de usuario neutros, sin implicación de dependencia 'companion' (D-10, accept) | smoke/audit | `grep -n "salida de consultas a base de datos" README.md docs/index.md`; `grep -n "encino-orm\|fetch_all\|fetch_many\|paginate" README.md docs/index.md; test $? -eq 1`; `uv run pytest -q && uv run ruff check` | ✅ README.md / docs/index.md | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

> Wave 0 (tests faltantes) está **embebida como Task 1 (RED) en cada plan**: el ejecutor crea los tests antes de tocar código fuente, y las pruebas de que fallan (exit != 0) son la verificación de esa tarea. DEP-01 se verifica por comando sobre archivos existentes — no requiere tests nuevos.

- [x] `tests/test_report_renderers.py` — Task 1 de 01-01 crea 6 tests de precisión CORR-02 (patrón `assert format_value(...)`, TESTING.md)
- [x] `tests/test_report.py` — Task 1 de 01-02 crea 2 tests `order_by` CORR-04/CORR-05 (patrón `pytest.raises(ValueError, ...)`)
- [x] `tests/test_security.py` — Task 1 de 01-01 crea banner `# --- P5: inyección de fórmulas con espacio/BOM ---` + 3 casos SEC-02 (guard `pytest.importorskip("openpyxl")` para el caso Excel)
- [x] Sin conftest, fixtures ni plugins nuevos — la infraestructura existente cubre todos los casos (convención TESTING.md: sin fixtures compartidas)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `uv lock` regenera y poda `encino-orm` + 5 transitivos (aiomysql, aiosqlite, asyncpg, async-timeout, pymysql) | DEP-01 (01-03-01) | Ejecución de herramienta de lock en el entorno dev; no es aserción de test | `git diff uv.lock` tras `uv lock`; confirmar que se eliminan exactamente esas 6 entradas y el `requires-dist` de `encino-rpt` (Pitfall 6: detenerse si hay cambios colaterales); `uv sync` para podar el venv; suite verde. |

*Otros: todos los comportamientos tienen verificación automatizada.*

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10 s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved