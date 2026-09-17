---
phase: 12-retirar-pydantic
verified: 2026-09-17T09:15:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
---

# Phase 12: Retirar pydantic — Verification Report

**Phase Goal:** Retirar `pydantic` — modelos como `dataclasses` stdlib, `to_dict`/`from_dict` propios, sin dependencias runtime (distribución ligera).
**Verified:** 2026-09-17T09:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (MIG-01..05)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | MIG-01: 13 modelos como `@dataclass` stdlib | ✓ VERIFIED | `encino_rpt/models.py` define 13 dataclasses (`Link`, `Image`, `Format`, `Total`, `Detail`, `Series`, `Chart`, `Pivot`, `ConditionalRule`, `Kpi`, `Group`, `ReportMeta`, `ReportResult`) con `from dataclasses import dataclass, field` (línea 5). Cero imports de pydantic. |
| 2 | MIG-02: `to_dict`/`to_json` serializan con coerción JSON (Decimal→str, datetime→iso) | ✓ VERIFIED | `encino_rpt/_serialize.py:44-47` convierte `Decimal→str` y `datetime/date/time→isoformat`. Comprobado en vivo: total `Decimal('350.75')` serializa a `'350.75'`. |
| 3 | MIG-03: round-trip `ReportResult.from_dict`/`from_json` con unión dispatch por `type` | ✓ VERIFIED | `_serialize.py:17-22` (`_NODES` dispatch `group/detail/chart/pivot`) + `_coerce` resuelve uniones. Round-trip con grupos+chart+pivot+link+image+kpi verificado: `ReportResult.from_dict(result.to_dict()).to_dict() == result.to_dict()`. |
| 4 | MIG-04: pydantic eliminado de `pyproject.toml` (deps + plugin mypy) | ✓ VERIFIED | `pyproject.toml` sin clave `dependencies` (pydantic era la única dep runtime), sin `plugins = ["pydantic.mypy"]` en `[tool.mypy]`, sin pydantic en `[dependency-groups]`. `uv.lock`: 0 referencias a pydantic. |
| 5 | MIG-05: suite + mypy + ruff verdes; round-trip validado; `from_dict` exportado | ✓ VERIFIED | `uv run pytest -q` → 115 passed. `uv run mypy encino_rpt` → Success (23 archivos). `uv run ruff check` → All checks passed. `uv run ruff format --check encino_rpt tests` → 28 files formatted. `ReportResult.from_dict` es callable y exportado vía `ReportResult` (en `__all__`). |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `encino_rpt/models.py` | 13 modelos `@dataclass` stdlib, sin pydantic | ✓ VERIFIED | 419 líneas, dataclasses + `__post_init__` para contexto interno (`_first_row`, `_header_tpl`, `_footer_tpl`) replicando `PrivateAttr`. |
| `encino_rpt/_serialize.py` | `to_jsonable` + `from_dict` | ✓ VERIFIED | 110 líneas; `to_jsonable` (coerción JSON) y `from_dict` (`_build`/`_coerce` con dispatch por discriminador `type`). |
| `encino_rpt/renderers/json.py` | Renderer JSON con `schema_version` usando `to_jsonable` | ✓ VERIFIED | `JsonRenderer.render`/`to_dict` delegan en `_serialize.to_jsonable`; inyecta `schema_version = "1.0"`. |
| `encino_rpt/__init__.py` | Re-exporta los 13 modelos + `Report`/`Reader` | ✓ VERIFIED | `__all__` lista 15 nombres públicos. |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `ReportResult.to_dict()` | `_serialize.to_jsonable` | lazy import (`models.py:172`) | ✓ WIRED |
| `ReportResult.from_dict()` | `_serialize.from_dict` | lazy import (`models.py:186`) | ✓ WIRED |
| `ReportResult.from_json()` | `from_dict` + `json.loads` | (`models.py:200-202`) | ✓ WIRED |
| `ReportResult.to_json()` | `JsonRenderer.render` | lazy import (`models.py:399`) | ✓ WIRED |
| `JsonRenderer.to_dict` | `_serialize.to_jsonable` | (`json.py:7,49`) | ✓ WIRED |
| `_serialize.from_dict` | dispatch unión `Group.children` | `_NODES` + `_coerce` | ✓ WIRED |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `ReportResult.to_dict()` | `to_jsonable(self)` | campos dataclass reales del árbol | Sí (Decimal/datetime coercidos, no vacíos) | ✓ FLOWING |
| `ReportResult.from_dict()` | `_build(ReportResult, data)` | dict de entrada → `_coerce` por type hints | Sí (reconstruye `Group`/`Detail`/`Chart`/`Pivot`/`Kpi`/`Link`/`Image`/`Format`/`Total`/`ReportMeta`) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| pydantic ausente en runtime | `uv run python -c "import encino_rpt; import sys; assert 'pydantic' not in sys.modules"` | `OK: pydantic not in sys.modules` | ✓ PASS |
| Suite completa | `uv run pytest -q` | `115 passed in 0.59s` | ✓ PASS |
| Type check | `uv run mypy encino_rpt` | `Success: no issues found in 23 source files` | ✓ PASS |
| Lint | `uv run ruff check` | `All checks passed!` | ✓ PASS |
| Formato | `uv run ruff format --check encino_rpt tests` | `28 files already formatted` | ✓ PASS |
| Round-trip con image+kpi | script inline (grupos+chart+pivot+link+image+kpi, Decimal) | `ROUND-TRIP OK`; Decimal → `'350.75'` | ✓ PASS |
| `from_dict` exportado | `uv run python -c "from encino_rpt import ReportResult; ..."` | `ReportResult.from_dict OK: True` | ✓ PASS |

### Requirements Coverage

| Requirement | Source | Description | Status | Evidence |
|-------------|--------|-------------|--------|---------|
| MIG-01 | hito v1.3 | 13 modelos `@dataclass` stdlib | ✓ SATISFIED | `models.py` (13 dataclasses, sin pydantic) |
| MIG-02 | hito v1.3 | `to_dict`/`to_json` con coerción JSON | ✓ SATISFIED | `_serialize.py:44-49`; spot-check Decimal→str |
| MIG-03 | hito v1.3 | round-trip `from_dict`/`from_json` (unión dispatch) | ✓ SATISFIED | `_serialize.py:17-22,70-98`; round-trip completo verificado |
| MIG-04 | hito v1.3 | pydantic fuera de `pyproject` (deps + plugin mypy) | ✓ SATISFIED | `pyproject.toml` sin `dependencies` ni `pydantic.mypy`; `uv.lock` sin pydantic |
| MIG-05 | hito v1.3 | suite/mypy/ruff verdes; round-trip; `from_dict` exportado | ✓ SATISFIED | 115 passed + mypy/ruff verdes; `ReportResult.from_dict` callable |

### Anti-Patterns Found

Ninguno. Sin marcadores `TBD`/`FIXME`/`XXX`/`PLACEHOLDER` ni stubs en los archivos migrados. Los únicos `return None` son rutas legítimas (guardas de streaming `file is None` en `models.py:244,295,326,359`, y ramas `None` de `_coerce`/`_discriminator` en `_serialize.py`).

Notas (no bloqueantes):
- `_serialize.py:1` y `models.py:170` mencionan "pydantic"/"model_dump" solo en docstrings históricos, no son imports.
- Los `.pyc` en `__pycache__/` que aún contienen la cadena "pydantic" son artefactos stale (gitignored); runtime confirmado sin pydantic en `sys.modules`.
- `from_dict` se exporta como classmethod de `ReportResult` (no como nombre top-level en `__all__`); es la entrada pública canónica documentada y usada por los tests.

### Human Verification Required

Ninguna. Refactor de librería pura, íntegramente verificable de forma programática (sin UI, sin servicio externo, sin comportamiento en tiempo real).

### Gaps Summary

Sin gaps. Los cinco must-haves del hito v1.3 están verificados contra el código real (no summaries): los 13 modelos son dataclasses stdlib, la serialización coerce `Decimal`/`datetime`, el round-trip reconstruye el árbol completo (grupos+chart+pivot+link+image+kpi), `pydantic` desapareció de `pyproject.toml` y `uv.lock`, y suite + mypy + ruff están verdes.

---

_Verified: 2026-09-17T09:15:00Z_
_Verifier: the agent (gsd-verifier)_
