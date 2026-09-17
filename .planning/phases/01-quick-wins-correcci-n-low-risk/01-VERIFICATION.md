---
phase: 01-quick-wins-correcci-n-low-risk
verified: 2026-09-16T20:30:00Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: null
gaps: []
human_verification: []
---

# Phase 01: Quick Wins (Corrección low-risk) Verification Report

**Phase Goal:** Eliminar bugs puntuales de corrección/seguridad de bajo riesgo sin tocar la arquitectura — números grandes conservan precisión, `order_by` funciona con funciones custom y con total ausente, el sanitizer CSV es robusto, y la dependencia muerta desaparece.
**Verified:** 2026-09-16T20:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP SC) | Status | Evidence |
|---|-------------------|--------|----------|
| 1 | `format_value` conserva precisión completa con `decimals=None` — `format_value(1234567.89, Format())` → `"1234567.89"`, no `"1.23457e+06"` | ✓ VERIFIED | Probe directo: `"1234567.89"`, miles `"1,234,567.89"`, currency-paren `"($1,234,567.89)"`, percent `"7%"`. Código: `encino_rpt/renderers/_format.py:28-34` — branch `decimals=None` usa `str(abs(value))` (D-01/D-02), `percent_scale` vía `Decimal(...)*100` + `format(d,"f")` (D-03). 6 tests de regresión `test_format_value_precision_*` en `tests/test_report_renderers.py:25-52` verdes. Sin matches de `:g` en `_format.py` (grep). |
| 2 | `order_by(expression=...)` evalúa con funciones custom registradas vía `add_function` — `doblado(monto)` ya no lanza `ExpressionError` | ✓ VERIFIED | Probe directo: `add_function("doblado", lambda v: v*2)` + `order_by(expression="doblado(total)", direction="desc")` → hijos `["Bob","Cid","Ana"]` sin excepción. Código: `encino_rpt/aggregation.py:260` (`_apply_order(spec, node.children, report._functions)`), `:281` (sorted key con `functions`), `:301` (`evaluate(expression, ..., functions)`). Test `test_order_by_expression_with_custom_function` (`tests/test_report.py:198`) verde. |
| 3 | `order_by(total=...)` con total inexistente lanza error claro que nombra el total, no `TypeError` crudo | ✓ VERIFIED | Probe directo: `order_by(total="total_inexistente")` → `ValueError: total de orden inexistente: 'total_inexistente' (hijo 'por_agente')` (nombra el total con `!r` + contexto del hijo; sin TypeError). Código: `encino_rpt/aggregation.py:294-299` — branch `total` de `_sort_key` hace `raise ValueError` en el primer hijo evaluado por `sorted()` (D-05/D-06). Test `test_order_by_missing_total_raises` (`tests/test_report.py:215`) verde. |
| 4 | El sanitizer CSV/Excel detecta caracteres peligrosos precedidos de espacio/BOM — `" =1+1"` y `"\x0c=1+1"` quedan saneados | ✓ VERIFIED | Probe directo: `is_dangerous(" =1+1")`, `is_dangerous("\x0c=1+1")`, `is_dangerous("\ufeff=1+1")`, `is_dangerous("\ufeff\t=1+1")` → True; `sanitize_csv(" =1+1")` → `"' =1+1"` (prefijo al valor ORIGINAL verbatim, D-09); `sanitize_csv("\x0c=1+1")` → `"'\x0c=1+1"`; `write_excel_cell` fuerza `data_type="s"` para `" =1+1"` y `"\ufeff@evil"`. Código: `encino_rpt/renderers/_sanitize.py:9` (`_LEADING_TRIM = re.compile(r"^[\s\ufeff]+")`), `:12-14` (is_dangerous post-recorte), fuente única compartida CSV+Excel (D-08). 3 tests P5 en `tests/test_security.py:32-57` verdes. Nota: `\x0c` en Excel lo rechaza openpyxl nativamente (`IllegalCharacterError`) antes de escribir — el bypass por control-char no alcanza la celda; el caso Excel probado usa `" =1+1"`/`"\ufeff@evil"` (ambos `data_type="s"`). |
| 5 | `encino-orm` eliminado de `pyproject.toml`; instalación nueva ya no arrastra esa dependencia | ✓ VERIFIED | `pyproject.toml:32-34` — `dependencies = ["pydantic>=2"]` (grep `encino-orm` → exit 1). `uv.lock` sin `encino-orm` ni los 5 transitivos (aiomysql, aiosqlite, asyncpg, async-timeout, pymysql → grep exit 1); `requires-dist` de encino-rpt solo `openpyxl` (extra) + `pydantic>=2` (líneas 256-258). **Prueba de instalación nueva:** `uv build --wheel` → METADATA del wheel declara únicamente `Requires-Dist: pydantic>=2` + extras `excel`/`pdf`; `encino-orm` ausente. README.md:4 y docs/index.md:4 con fraseo neutro (`salida de consultas a base de datos, sin acoplarse al motor`), 0 matches de `fetch_all|fetch_many|paginate|encino-orm`. `paginate` en uv.lock es el paginador de mkdocs, no relacionado. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `encino_rpt/renderers/_format.py` | Branch `decimals=None` con `str()` y escala percent vía Decimal | ✓ VERIFIED | `:30` `Decimal(str(abs(value))) * 100).normalize()`, `:34` `str(abs(value))`; `_add_thousands` intacto; sin `:g` |
| `encino_rpt/renderers/_sanitize.py` | `is_dangerous` post-recorte whitespace+BOM | ✓ VERIFIED | `:9` `_LEADING_TRIM`, `:14` trim + `startswith`; `sanitize_csv`/`write_excel_cell` intactos (`:20` prefijo `'` verbatim, `:31` `data_type="s"`) |
| `encino_rpt/aggregation.py` | `_apply_order`/`_sort_key` con `functions` + raise en total ausente | ✓ VERIFIED | `:277` `_apply_order(spec, children, functions)`, `:290` `_sort_key(child, ob, functions)`, `:299` `raise ValueError`, `:260` call site con `report._functions` |
| `tests/test_report_renderers.py` | 6 tests de precisión CORR-02 | ✓ VERIFIED | `:25-52` `test_format_value_precision_*` |
| `tests/test_security.py` | 3 tests P5 SEC-02 | ✓ VERIFIED | `:32-57` is_dangerous/sanitize_csv/excel con espacio/BOM |
| `tests/test_report.py` | 2 tests order_by CORR-04/CORR-05 | ✓ VERIFIED | `:198` custom-function, `:215` missing-total raises |
| `pyproject.toml` | dependencies sin encino-orm, solo `pydantic>=2` | ✓ VERIFIED | `:32-34` |
| `uv.lock` | Lock sin encino-orm ni transitivos | ✓ VERIFIED | grep exit 1 en los 6 paquetes; page `paginate` (mkdocs) conservado |
| `README.md` / `docs/index.md` | Fraseo neutro del contrato de entrada | ✓ VERIFIED | Ambas línea 4: `salida de consultas a base de datos, sin acoplarse al motor`; sin referencias ORM |
| `docs/security.md` | Descripción del sanitizer actualizada | ✓ VERIFIED | `:34` "ignora los espacios en blanco y BOM" |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| `sanitize_csv` | `is_dangerous` | detección compartida (D-08) | ✓ WIRED | `_sanitize.py:19` llama `is_dangerous` |
| `write_excel_cell` | `is_dangerous` | detección compartida (D-08) | ✓ WIRED | `_sanitize.py:30` llama `is_dangerous` |
| `format_value` | `_add_thousands` | miles sobre texto de precisión completa | ✓ WIRED | `_format.py:36`; probe `"1,234,567.89"` OK |
| call site `aggregation.py:260` | `_apply_order` | threading de `report._functions` | ✓ WIRED | `_apply_order(spec, node.children, report._functions)` |
| `_sort_key` | `evaluate` | contexto de orden con funciones | ✓ WIRED | `:301` `evaluate(expression, getattr(child, "_first_row", {}), functions)` |
| `_sort_key` branch total | `ValueError` | error claro en español con `!r` | ✓ WIRED | `:299` `raise ValueError(f"total de orden inexistente: {total!r} (hijo {child_desc!r})")` |
| `pyproject.toml` dependencies | `uv.lock` requires-dist | regeneración `uv lock` | ✓ WIRED | requires-dist solo `openpyxl` (extra) + `pydantic>=2` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| `format_value` | `value` → `text` | valor de fila real (probe con float 1234567.89, 0.07, negativos) | Sí — transformación pura verificada por probes directos | ✓ FLOWING |
| `_sort_key` expression | `_first_row` + `functions` | filas reales de `Report(rows)`, funciones de `add_function` | Sí — probe end-to-end `["Bob","Cid","Ana"]` | ✓ FLOWING |
| `_sort_key` total | `child.totals` | `Total` reales del pipeline de agregación | Sí — raise solo cuando el total realmente no existe (probe) | ✓ FLOWING |
| `is_dangerous`/`sanitize_csv` | `value` | cadenas de datos no confiables | Sí — probe `" =1+1"`/`"\x0c=1+1"`/`"\ufeff@evil"` | ✓ FLOWING |
| `write_excel_cell` | `cell` | openpyxl cell real (probe Workbook) | Sí — `data_type="s"` observado | ✓ FLOWING |

No stubs, no hollow props, no disconnected data sources detectados.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| SC1 precision completa | `uv run python -c "...format_value(1234567.89, Format())..."` | `1234567.89 | 1,234,567.89 | ($1,234,567.89) | 7%` | ✓ PASS |
| SC2 order_by con función custom | probe Report + add_function + order_by(expression=...) | `order = ['Bob', 'Cid', 'Ana']` | ✓ PASS |
| SC3 total inexistente | probe order_by(total="total_inexistente") | `ValueError: total de orden inexistente: 'total_inexistente' (hijo 'por_agente')` — no TypeError | ✓ PASS |
| SC4 sanitizer espacio/BOM | probe is_dangerous + sanitize_csv + write_excel_cell | 5 detecciones True, prefijo verbatim, `data_type="s"` | ✓ PASS |
| SC5 dependencia muerta | grep pyproject/uv.lock + `uv build --wheel` + inspección METADATA | 0 matches; METADATA: `Requires-Dist: pydantic>=2` (+extras) | ✓ PASS |
| Suite completa | `uv run pytest -q` | `43 passed in 0.29s` | ✓ PASS |
| Lint | `uv run ruff check` | `All checks passed!` | ✓ PASS |

### Probe Execution

No probes declarados en PLAN/SUMMARY de esta fase (los planes usan tests RED/GREEN + comandos de verificación directos). Step 7c: SKIPPED (no probe scripts en `scripts/`, sin criterios de probes en la fase).

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| CORR-02 | 01-01 | `format_value` conserva precisión completa con `decimals=None` | ✓ SATISFIED | SC1: `_format.py:28-34` + 6 tests + probe |
| SEC-02 | 01-01 | Sanitizer detecta caracteres peligrosos precedidos de espacio/BOM | ✓ SATISFIED | SC4: `_sanitize.py:9-14` + 3 tests P5 + probe |
| CORR-04 | 01-02 | `order_by(expression=...)` evalúa con funciones custom | ✓ SATISFIED | SC2: `aggregation.py:260,281,301` + test + probe |
| CORR-05 | 01-02 | `order_by(total=...)` con total inexistente lanza error claro | ✓ SATISFIED | SC3: `aggregation.py:294-299` + test + probe |
| DEP-01 | 01-03 | Dependencia muerta `encino-orm` eliminada | ✓ SATISFIED | SC5: pyproject/uv.lock/wheel METADATA sin encino-orm |

**Orphan check:** ROADMAP asigna exactamente CORR-02, CORR-04, CORR-05, SEC-02, DEP-01 a Phase 1; los planes 01-01/01-02/01-03 los reclaman todos. 0 requisitos huérfanos.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| — | — | Ninguno — grep de `TBD|FIXME|XXX|HACK|PLACEHOLDER|not implemented|coming soon` en los 10 archivos tocados: 0 matches | — | — |

### Code-Review Caveats (01-REVIEW.md) — confirmación de no-conflicto

- **WR-01** (warning, no bloqueante): el `raise` de CORR-05 ahora también aborta `run()` en usos antes tolerados (sección con hijos `Detail` sin totales; subgrupos mixtos donde solo algunos declaran el total ordenado). **No contradice must-haves**: D-06 estaba bloqueado explícitamente ("error en el primer hijo faltante, política ruidosa no silenciosa") y el SC3 solo exige error claro que nombre el total. Comportamiento deliberado del plan, ya documentado en REVIEW para fases futuras (Phase 3 Robustez, CORR-06).
- **WR-02** (warning, no bloqueante): el branch `column` de `_sort_key` sigue devolviendo `None` → `TypeError` crudo de `sorted()` para filas sin la columna. **No contradice CORR-05**: el SC3/aceptación está acotado a `order_by(total=...)` con nombre inexistente, y el probe confirma que el branch `total` lanza el `ValueError` nombrando el total. El branch `column` (configuración `order_by(column=...)`) está fuera del alcance declarado de la fase; llevar a Phase 3 (modos de fallo silencioso / errores con contexto).
- IN-01/IN-02: info, sin impacto en los must-haves.

### Human Verification Required

Ninguno. Librería Python pura, determinista, sin UI ni servicios externos; los 5 criterios se verificaron con probes directos contra el código vivo, la suite completa (43 tests) y auditoría de grep/build del artefacto de instalación.

### Gaps Summary

Sin gaps. Los 5 criterios de éxito del ROADMAP están verificados empíricamente contra el código, la suite (43 passed), ruff (clean), y el artefacto wheel (METADATA sin encino-orm). Commits de los 3 planes verificados en `git log` (98fbc19, 781b1ef, a2447a3, 0514241, 83698ad, 0858169, aa7e534). Único residuo: snapshots GSD (`AGENTS.md`, `.planning/codebase/*.md`) aún describen encino-orm como dependencia declarada — esperado y documentado en 01-03-SUMMARY (se regeneran con el próximo escaneo GSD, no se editan a mano).

---

_Verified: 2026-09-16T20:30:00Z_
_Verifier: the agent (gsd-verifier)_