---
phase: 08-tests-ci
reviewed: 2026-09-16T22:30:00Z
depth: deep
files_reviewed: 24
files_reviewed_list:
  - .github/workflows/ci.yml
  - pyproject.toml
  - uv.lock
  - encino_rpt/__init__.py
  - encino_rpt/_specs.py
  - encino_rpt/aggregation.py
  - encino_rpt/expressions.py
  - encino_rpt/models.py
  - encino_rpt/pivot.py
  - encino_rpt/renderers/__init__.py
  - encino_rpt/renderers/_format.py
  - encino_rpt/renderers/_sanitize.py
  - encino_rpt/renderers/csv.py
  - encino_rpt/renderers/excel.py
  - encino_rpt/renderers/html.py
  - encino_rpt/renderers/pdf.py
  - encino_rpt/renderers/text.py
  - encino_rpt/report.py
  - encino_rpt/section.py
  - encino_rpt/template.py
  - tests/test_perf_smoke.py
  - tests/test_report.py
  - tests/test_report_renderers.py
  - tests/test_security.py
findings:
  critical: 0
  major: 0
  minor: 0
  info: 3
  total: 3
status: clean
---

# Phase 08: Code Review Report

**Reviewed:** 2026-09-16T22:30:00Z
**Depth:** deep
**Files Reviewed:** 24
**Status:** clean

## Summary

Revisé el diff completo de la fase 08 (`a4c9cfe..HEAD`) — no resúmenes. Los cambios de código fuente (`encino_rpt/`) provienen de exactamente dos commits: `4b76ae3` (normalización `ruff format`, solo whitespace/ajuste de línea/comas finales) y `2c8500d` (triage de mypy, solo anotaciones de tipos). No hay cambios de lógica en la librería. Verifiqué los 5 gates de CI localmente y **todos pasan**:

1. `uv run pytest -q` → **79 passed, 3 xfailed** (exit 0)
2. `uv run ruff check` → **All checks passed**
3. `uv run mypy encino_rpt` → **Success: no issues found in 20 source files**
4. `uv run ruff format --check encino_rpt tests` → **24 files already formatted**
5. `uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80` → **TOTAL 84%** (83.87%), ≥ 80%

La fase es sólida. No encontré defectos de corrección, seguridad ni regresiones de comportamiento. Los 3 hallazgos que siguen son observaciones *info* (no bloqueantes).

### Verificación de los tres focos solicitados

- **Correctitud de las anotaciones mypy (sin cambios de comportamiento):** confirmada. Revisé cada anotación añadida y son solo-tipo (locales, no evaluadas en runtime; `from __future__ import annotations` cubre las de nivel módulo). El único cambio "cercano a lógica" es `op`→`uop` en la rama `ast.UnaryOp` de `expressions.py` (línea 95), un renombre puro que resuelve un *clash* de tipos binario/unario que mypy reportaba sobre la misma variable `op`; el comportamiento es idéntico (cubierto por `test_expression_arithmetic` → `-cantidad`). El alias `Child = Detail | Group | Chart | Pivot` (`aggregation.py:27`) coincide exactamente con la unión real `Group.children: list[Detail | Group | Chart | Pivot]` (`models.py:121`).
- **CI workflow correcto:** confirmada. `ci.yml` tiene dos jobs (`test` matrix 3.10–3.13 sin cambios; `quality` singleton 3.13 con `mypy` + `ruff format --check` + coverage), sin `needs`, YAML bien indentado, acciones pineadas (`checkout@v4`, `setup-uv@v4`). `mypy>=2.3.1`, `pytest-cov>=7.1.0` y `coverage` están bloqueados en `uv.lock` (líneas 907/1305/295).
- **Tests significativos (no tautológicos):** confirmada. Los 11 tests nuevos ejercitan rutas reales con asertos de valor concreto, y los `xfail(strict=True)` codifican el comportamiento *correcto* que hoy falla. Los comentarios `# CONCERNS.md` referencian secciones que existen y describen con precisión cada bug.

---

## Info

### IN-01: `disable_error_code = ["import-untyped"]` es una relajación global, no por-módulo

**File:** `pyproject.toml:71`
**Issue:** El `import-untyped` queda deshabilitado para **toda** importación de módulos sin tipos, no solo para `openpyxl`/`reportlab`. Si en el futuro se añade una dependencia opcional sin stubs y se importa, mypy no lo señalará. Hoy es inofensivo (las únicas importaciones sin tipos son las dos deps opcionales lazy) y está documentado en el comentario y en `08-04-SUMMARY.md` (desviación justificada para evitar fricción con ruff `I001`), pero una alternativa más precisa sería un override por-módulo.
**Fix (opcional):**
```toml
[[tool.mypy.overrides]]
module = ["openpyxl.*", "reportlab.*"]
ignore_missing_imports = true
```

### IN-02: Tres tests "documentan bug" fijan comportamiento buggy sin `xfail`

**File:** `tests/test_report.py:471` (`test_suppress_zero_missing_column`), `tests/test_report.py:502` (`test_count_expression_semantics`), `tests/test_report.py:528` (`test_unhashable_group_value`)
**Issue:** Estos tres tests asertan el comportamiento **actual defectuoso** (`len(children) == 0`, `totals[0].value == 1`, `pytest.raises(TypeError)`) y pasan hoy. Cuando se corrijan los bugs, estos tests **fallarán** y obligarán al que los corrija a actualizarlos (que es la intención explícita del plan 08-01: "un fix futuro sea un cambio detectable"). Es un patrón de documentación deliberado y los comentarios en español lo dejan claro, pero conviene que quien toque `_is_zero`/`_partition`/`_value_for` sepa que estos tests deben invertirse (a `xfail` o a assert del comportamiento correcto) junto con el fix.
**Fix:** No se requiere cambio ahora; dejar registro en el PR que corrija cada bug para que flipe el assert correspondiente.

### IN-03: El job `quality` re-ejecuta la suite completa (incluido el smoke de 50k) por el gate de cobertura

**File:** `.github/workflows/ci.yml:52-53`
**Issue:** `pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80` vuelve a correr la suite entera (incluyendo `test_perf_smoke.py`). En total la suite corre 5× por push (4 matrix + 1 quality). No es un defecto — es el patrón estándar para medir cobertura en un job separado — y el smoke (~0.14s) es despreciable frente al límite de 10s, pero es redundancia que se podría acotar si el tiempo de CI llegara a importar.
**Fix:** Opcional: dejar `--cov` solo en el job `quality` y excluir el smoke de la repetición (`-m "not perf"` con un marker), o aceptar la redundancia actual (recomendado, mantiene la cobertura simple).

---

_Reviewed: 2026-09-16T22:30:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: deep_
