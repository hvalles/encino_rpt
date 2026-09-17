---
phase: 01
slug: quick-wins-correcci-n-low-risk
status: draft
nyquist_compliant: false
wave_0_complete: false
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

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | CORR-02 | — | N/A | unit | `uv run pytest tests/test_report_renderers.py -x -k format_value` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | CORR-04 | — | N/A | unit | `uv run pytest tests/test_report.py -x -k order_by` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | CORR-05 | — | N/A | unit | `uv run pytest tests/test_report.py -x -k order_by` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | SEC-02 | T-01-01 | `is_dangerous` post-recorte whitespace/BOM; CSV prefijo `'` sobre valor original; Excel `data_type='s'` | unit | `uv run pytest tests/test_security.py -x` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | DEP-01 | — | N/A | smoke | `grep -n encino-orm pyproject.toml uv.lock; uv run pytest -q` | ✅ pyproject.toml | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_report_renderers.py` — añadir tests de precisión CORR-02 (patrón existente `assert format_value(...)`)
- [ ] `tests/test_report.py` — añadir tests `order_by` CORR-04/CORR-05 (patrón `pytest.raises(ValueError, ...)`)
- [ ] `tests/test_security.py` — añadir banner `# --- P5: inyección de fórmulas con espacio/BOM ---` y casos SEC-02 (guard `pytest.importorskip("openpyxl")` para el caso Excel)
- [ ] Sin conftest, fixtures ni plugins nuevos — la infraestructura existente cubre todos los casos (convención TESTING.md: sin fixtures compartidas)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `uv lock` regenera y poda `encino-orm` + 5 transitivos (aiomysql, aiosqlite, asyncpg, async-timeout, pymysql) | DEP-01 | Ejecución de herramienta de lock en el entorno dev; no es aserción de test | `git diff uv.lock` tras `uv lock`; confirmar que se eliminan exactamente esas 6 entradas y el `requires-dist` de `encino-rpt`; `uv sync` para podar el venv; suite verde. |

*Otros: todos los comportamientos tienen verificación automatizada.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10 s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending