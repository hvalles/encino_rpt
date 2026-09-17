---
phase: 11-engine-bug-fixes
verified: 2026-09-17T14:00:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
---

# Phase 11: Engine Bug Fixes Verification Report

**Phase Goal:** Corregir 7 bugs de correctitud del motor (CORR-08..14): `detail(source=)`, crash de totales `None`, contexto en chart/pivot, columna de `suppress_zero` inexistente, agrupación no-hashable, semántica de `count`, y serialización JSON profunda.

**Verified:** 2026-09-17
**Status:** passed
**Re-verification:** No — initial verification (no prior VERIFICATION.md present)

## Goal Achievement

### Observable Truths

| #   | Truth                                                                 | Status     | Evidence |
| --- | --------------------------------------------------------------------- | ---------- | -------- |
| 1   | `detail(source=X)` funciona a nivel raíz (sin grupos)                  | ✓ VERIFIED | `report.py:331-345` almacena `_detail_source`; `aggregation.py:598-601` fija `source` del root spec vía `dataclasses.replace`. Test `test_detail_source_ignored` (`test_report.py:487`) asevera `row["sku"] == "B"`. Spot-check: detalle del dataset `presupuesto` renderiza `B`. |
| 2   | `detail(source=X)` + grupos lanza `ValueError`                          | ✓ VERIFIED | `aggregation.py:593-597` lanza `ValueError("detail(source=...) no es compatible con grupos...")` cuando `children_map` no vacío. Test `test_detail_source_with_groups_raises` (`test_report.py:499`). |
| 3   | total nombrado `None` no rompe el registro (`0 + None`)                | ✓ VERIFIED | `aggregation.py:256` usa `registry.get(key, 0) + (val if val is not None else 0)`. Test `test_named_total_none_values` (`test_report.py:528`). Spot-check: deferred `TOTAL("por_g.promedio")` resuelve a `0` (no crash). |
| 4   | errores de chart/pivot envueltos con contexto de grupo                | ✓ VERIFIED | `aggregation.py:380-397` envuelve `build_chart`/`build_pivot` en `_wrap(f"gráfico (grupo …)"/"pivote (grupo …)")`. Test `test_chart_pivot_error_context` (`test_report.py:551`). Spot-check pivot: `AggregationError: pivote (grupo 'global'): error aritmético: division by zero`. |
| 5   | `suppress_zero` con columna inexistente lanza `ValueError`             | ✓ VERIFIED | `aggregation.py:458-487` (`_is_zero`) lanza `ValueError("columna de suppress_zero inexistente: …")`. Test `test_suppress_zero_missing_column` (`test_report.py:471`). |
| 6   | agrupación/pivote con valor no-hashable lanza `ValueError` claro       | ✓ VERIFIED | `aggregation.py:192-204` (`_partition`) valida `hash(key)`; `pivot.py:63-75` (`_assert_hashable`). Test `test_unhashable_group_value` (`test_report.py:539`). Spot-check pivot: `ValueError: valor no hashable en la columna de pivote …`. |
| 7   | semántica de `count` documentada y consistente                         | ✓ VERIFIED | `aggregation.py:71-96` (`_value_for`) docstring: `count` sin expresión = `len(rows)`; `count`+expresión = conteo truthy (`aggregation.py:88-89`). Test `test_count_expression_semantics` (`test_report.py:513`): `positivos == 1`, `filas == 3`. |
| 8   | `to_json()` profundo lanza `ValueError` claro (no `RecursionError`)     | ✓ VERIFIED | `renderers/json.py:32-49` envuelve `model_dump`/`json.dumps` en try/except `RecursionError`/`ValueError` → `ValueError(_DEPTH_ERROR)`. Test `test_deep_tree_to_json` (`test_report_renderers.py:436`, 1100 niveles). Spot-check: 1200 niveles → `ValueError: la jerarquía es demasiado profunda...`. |
| 9   | los 3 xfail previos pasan; ningún `xfail` restante                     | ✓ VERIFIED | `grep xfail tests/` → sin coincidencias. Los 3 tests convertidos a asserts (`test_detail_source_ignored`, `test_named_total_none_values`, `test_chart_pivot_error_context`) están en verde. |

**Score:** 8/8 truths verified (7 CORR + 1 verificación-xfail)

### Required Artifacts

| Artifact                      | Expected                                        | Status    | Details |
| ----------------------------- | ----------------------------------------------- | --------- | ------- |
| `encino_rpt/aggregation.py`   | fixes CORR-09/10/11/12 + detail source raíz     | ✓ VERIFIED | `_wrap` chart/pivot, `_is_zero` fail-loudly, `_partition` valida hash, guard de `None`, `_value_for` docstring, `build()` fija `detail_source` |
| `encino_rpt/report.py`        | `detail()` almacena `source`                    | ✓ VERIFIED | `_detail_source` en `__init__` (:36) y `detail()` (:331-345) |
| `encino_rpt/pivot.py`         | `_assert_hashable` en `build_pivot`             | ✓ VERIFIED | `_assert_hashable` (:63-75) usado en valores row/col |
| `encino_rpt/renderers/json.py`| `ValueError` controlado en `to_dict`/`render`   | ✓ VERIFIED | `_DEPTH_ERROR` + try/except (:32-49) |
| `tests/test_report.py`        | xfail → asserts verdes                          | ✓ VERIFIED | 6 tests de regresión + 2 asserts de `ValueError` |
| `tests/test_report_renderers.py` | `test_deep_tree_to_json`                     | ✓ VERIFIED | :436-448 |

### Key Link Verification

| From                       | To                     | Via                                        | Status | Details |
| -------------------------- | ---------------------- | ------------------------------------------ | ------ | ------- |
| `aggregation.py` (fixes)   | `tests/test_report.py` | xfail convertido a assert                   | ✓ WIRED | `grep xfail tests/` → vacío; 113 passed |
| `report.py` `_detail_source` | `aggregation.py` `build()` | `build()` lee `report._detail_source`      | ✓ WIRED | :593-601 |
| `json.py` `to_dict`        | `models.py` `to_json`  | `to_json` → `JsonRenderer.to_dict`         | ✓ WIRED | docstring documenta límite en `models.py` |

### Data-Flow Trace (Level 4)

No aplica — fase de correctitud/guardas de error; no introduce renderizado de datos nuevos. El flujo `detail(source=)` sí se traza: `add_dataset("presupuesto")` → `_enrich(report, "presupuesto")` (`aggregation.py:589-590`) → `sources[name]` → `_build_group` selecciona `sources[spec.source]` (`aggregation.py:213`) → `Detail` del dataset correcto (verificado por spot-check: `sku == "B"`).

### Behavioral Spot-Checks

| Behavior                                          | Command | Result | Status |
| ------------------------------------------------- | ------- | ------ | ------ |
| `detail(source=)` usa el dataset indicado         | `rep.detail("sku","monto", source="presupuesto").run()` | `sku == "B"` | ✓ PASS |
| deferred `TOTAL` con None acumula 0               | `TOTAL("por_g.promedio")` sobre avg None | resuelve `0` | ✓ PASS |
| `to_json()` 1200 niveles → ValueError             | `result.to_json()` | `ValueError: la jerarquía es demasiado profunda...` | ✓ PASS |
| pivot valor no-hashable → ValueError              | `.pivot('r','c',...)` con `r=['x']` | `ValueError: valor no hashable en la columna de pivote...` | ✓ PASS |
| pivot expresión inválida → AggregationError       | `value_expression='1/(monto-1)'` | `AggregationError: pivote (grupo 'global'): ...` | ✓ PASS |

### Probe Execution

No aplica — fase de biblioteca pura sin `scripts/*/tests/probe-*.sh` ni probes declarados en PLAN/SUMMARY.

### Requirements Coverage

| Requirement | Descripción (REQUIREMENTS.md)                        | Status      | Evidence |
| ----------- | ---------------------------------------------------- | ----------- | -------- |
| CORR-08     | `detail(source=...)` usa el dataset indicado          | ✓ SATISFIED  | `aggregation.py:593-601` + tests :487/:499 |
| CORR-09     | totales `None` no rompen el acumulador                | ✓ SATISFIED  | `aggregation.py:256` + test :528 |
| CORR-10     | chart/pivot envuelto con contexto (`_wrap`)           | ✓ SATISFIED  | `aggregation.py:380-397` + test :551 |
| CORR-11     | `suppress_zero` columna inexistente → error claro     | ✓ SATISFIED  | `aggregation.py:466-487` + test :471 |
| CORR-12     | no-hashable → error claro (no `TypeError`)            | ✓ SATISFIED  | `aggregation.py:192-204` + `pivot.py:63-75` + test :539 |
| CORR-13     | `count`+`expression` semántica documentada            | ✓ SATISFIED  | `aggregation.py:71-96` docstring + test :513 |
| CORR-14     | jerarquías profundas → error claro (no `RecursionError`) | ✓ SATISFIED | `json.py:32-49` + test `test_deep_tree_to_json` |

No hay requirements huérfanos para Phase 11 (los 7 CORR-08..14 declarados en PLAN frontmatter coinciden con REQUIREMENTS.md).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| —    | —    | —       | —        | Ninguno |

No se detectaron marcadores de deuda (`TBD`/`FIXME`/`XXX`/`TODO`/placeholder), implementaciones vacías ni valores hardcodeados vacíos en los archivos modificados por esta fase.

### Gaps Summary

Ninguno. Los 7 bugs de correctitud (CORR-08..14) están corregidos y cubiertos por regresiones verdes; los 3 `xfail` previos pasaron a asserts verdes y no queda ningún `xfail` en `tests/`. La suite completa, `mypy`, `ruff check` y `ruff format --check` pasan limpiamente.

**Comandos de verificación ejecutados (propios):**
- `uv run pytest -q` → **113 passed** in 7.09s
- `uv run mypy encino_rpt` → **Success: no issues found in 22 source files**
- `uv run ruff check` → **All checks passed!**
- `uv run ruff format --check encino_rpt tests` → **27 files already formatted**

---

_Verified: 2026-09-17_
_Verifier: the agent (gsd-verifier)_
