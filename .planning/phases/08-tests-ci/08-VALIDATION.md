---
phase: 08
slug: tests-ci
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-09-17
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — `testpaths=["tests"]`, `pythonpath=["."]` |
| **Quick run command** | `uv run pytest -q` |
| **Full suite command** | `uv run pytest && uv run ruff check` |
| **Estimated runtime** | ~1 s suite (70 tests) + ~2 s ruff |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

> Se completa tras el planner (los comandos de la columna *Automated Command* son los `<verify><automated>` de cada plan). Placeholder hasta el paso 8.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| *pendiente* | — | — | TEST-01, TEST-02 | — | — | — | — | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

> Placeholder — se concreta tras el planner. Investigación (08-RESEARCH.md) ya detecta: `ruff format .` hoy barre 40+ archivos fuente + 17 `.md`; se necesita normalización one-time de formato ANTES de añadir el gate de CI.

- [ ] Normalización one-time `ruff format` (scope `encino_rpt tests`, `extend-exclude` para `.md` de `.planning/`/`docs/`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI end-to-end verde (matrix 3.10–3.13 + job `quality` con mypy/format/coverage) | TEST-02 | Ejecución real de GitHub Actions en push; no es aserción local | Push de rama → revisar `.github/workflows/ci.yml` verde; verificar que el job `quality` corre una sola vez y el smoke de 50k filas pasa |

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
