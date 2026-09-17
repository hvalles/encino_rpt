# Phase 1: Quick Wins (Corrección low-risk) — Pattern Map

**Mapped:** 2026-09-16
**Files analyzed:** 10 (3 código fuente, 2 config/build, 3 tests, 2 docs)
**Analogs found:** 8 / 8 archivos editables (2 regenerados por herramienta: `uv.lock`)

> Naturaleza de la fase: **modificación de archivos existentes** (cirugía mínima, call sites únicos verificados). Cada archivo es su propio analog (self-analog); los patrones de referencia provienen de sitios hermanos dentro del mismo módulo. No se crean archivos nuevos.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `encino_rpt/renderers/_format.py` | utility | transform | self (líneas 9-39 `format_value`, 42-48 `_add_thousands`) + patrón Decimal ya importado (línea 6) | exact |
| `encino_rpt/renderers/_sanitize.py` | utility | transform | self (líneas 8-10 `is_dangerous`, 13-17 `sanitize_csv`, 20-27 `write_excel_cell`) | exact |
| `encino_rpt/aggregation.py` | service | transform | self — patrón evaluate-threading en líneas 102/174/266/270/365/396; `_apply_order`/`_sort_key` 277-307 son los sitios divergentes | exact |
| `pyproject.toml` | config | n/a | self (líneas 32-35 `dependencies`) | exact |
| `uv.lock` | config | n/a | regenerado por `uv lock` (no editable a mano) | n/a |
| `tests/test_report.py` | test | n/a | `test_order_top_suppress` (182-195) + `test_expression_rejects_unsafe` (32-38, patrón `pytest.raises`) | exact |
| `tests/test_report_renderers.py` | test | n/a | `test_format_value_currency/percent/number` (8-22) | exact |
| `tests/test_security.py` | test | n/a | `test_csv_formula_injection` (9-15) + `test_excel_formula_injection` (18-27, `importorskip`) | exact |
| `docs/security.md` | docs | n/a | self (sección sanitizer 30-41) | exact |
| `README.md` + `docs/index.md` | docs | n/a | self (línea 4 de cada uno; re-fraseo neutro opcional DEP-01) | exact |

## Pattern Assignments

### `encino_rpt/renderers/_format.py` (utility, transform) — CORR-02

**Analog:** self (el archivo a modificar). El branch a reemplazar es `format_value` líneas 21-29; el patrón de miles ya existe en `_add_thousands` 42-48.

**Imports pattern** (líneas 1-6) — `Decimal` ya está importado; no añadir nada:
```python
"""Formateo de valores según `Format` (lo aplican los renderers)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
```

**Core pattern a reemplazar** (líneas 21-29) — el bug es `f"{abs(num):g}"` en la línea 29:
```python
    if isinstance(value, (int, float, Decimal)):
        num = value
        if fmt.percent_scale:
            num = num * 100
        neg = num < 0
        if fmt.decimals is not None:
            text = f"{abs(num):.{fmt.decimals}f}"
        else:
            text = f"{abs(num):g}"          # ← BUG: sci prematura (1.23457e+06)
```

**Reemplazo verificado por research** (Research §Code Examples 1, líneas 281-295) — el resto del flujo (thousands/percent/symbol/negative, líneas 30-38) NO cambia:
```python
    if fmt.decimals is not None:
        num = value
        if fmt.percent_scale:
            num = num * 100
        text = f"{abs(num):.{fmt.decimals}f}"
    elif fmt.percent_scale:
        # escala exacta sin artefactos binarios: 0.07*100 -> "7", nunca "7.000000000000001"
        d = (Decimal(str(abs(value))) * 100).normalize()
        text = format(d, "f")
    else:
        # repr round-trip corto; sci solo en |num|>=1e16 o <1e-4 (D-02)
        text = str(abs(value))
```

**Chained pattern** (líneas 30-38) — intacto; `_add_thousands` (42-48) ya tolera sci con try/except:
```python
        if fmt.thousands:
            text = _add_thousands(text)
        if fmt.kind == "percent":
            text = f"{text}%"
        if fmt.symbol:
            text = (fmt.symbol + text) if fmt.symbol_position == "prefix" else (text + fmt.symbol)
        if neg:
            text = f"({text})" if fmt.negative == "paren" else f"-{text}"
```

---

### `encino_rpt/renderers/_sanitize.py` (utility, transform) — SEC-02

**Analog:** self. El cambio se limita a `is_dangerous` (8-10) + añadir `import re`; `sanitize_csv` y `write_excel_cell` NO se tocan (D-08 fuente única de verdad).

**Imports pattern** (líneas 1-5) — añadir `import re` tras el `from __future__` (orden: stdlib, blank, relativo — convención CONVENTIONS.md):
```python
"""Mitigación de inyección de fórmulas en Excel/CSV (OWASP)."""

from __future__ import annotations

import re

_DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
```

**Core pattern a reemplazar** (líneas 8-10) — el bug es `value.startswith(...)` (chequeo de primer byte; BOM y whitespace lo burlan):
```python
def is_dangerous(value) -> bool:
    """True si `value` es una cadena que Excel/Calc podría tratar como fórmula."""
    return isinstance(value, str) and value.startswith(_DANGEROUS_PREFIXES)
```

**Reemplazo verificado por research** (Research §Code Examples 2, líneas 303-307):
```python
_LEADING_TRIM = re.compile(r"^[\s\ufeff]+")

def is_dangerous(value) -> bool:
    """True si Excel/Calc podría tratar `value` como fórmula tras ignorar espacios/BOM iniciales."""
    return isinstance(value, str) and _LEADING_TRIM.sub("", value).startswith(_DANGEROUS_PREFIXES)
```

**Consumer pattern — NO tocar** (líneas 13-17 y 20-27). `sanitize_csv` ya prefija el valor ORIGINAL (D-09 ✓); `write_excel_cell` ya fuerza `data_type = "s"` (D-08 ✓):
```python
def sanitize_csv(value):
    """Prefija `'` a cadenas peligrosas para que el CSV se importe como texto."""
    if is_dangerous(value):
        return "'" + value          # valor original verbatim + prefijo (D-09)
    return value


def write_excel_cell(cell, value):
    cell.value = value
    if is_dangerous(value):
        cell.data_type = "s"        # forzado a texto (D-08)
    return cell
```

---

### `encino_rpt/aggregation.py` (service, transform) — CORR-04 / CORR-05

**Analog:** self. El patrón de function-threading ya existe en 5 sitios; `_sort_key` (línea 300) es el único que pasa `{}`. El call site único de `_apply_order` es la línea 260 (dentro de `_build_instance`, que ya recibe `report`).

**Reference pattern — evaluate-threading** (el patrón a alinear; pasan `report._functions`):

`aggregation.py:102` (en `_enrich`):
```python
                val = evaluate(f.expression, enriched, report._functions)
```

`aggregation.py:166-179` (en `_compute_totals_into` — el patrón de referencia para CORR-04):
```python
def _compute_totals_into(report, spec, rows, node, registry, deferred):
    for ts in spec.totals:
        if ts.expression and "TOTAL(" in ts.expression:
            total = _make_total(ts, None)
            deferred.append((total, ts, rows))
            node.totals.append(total)
        else:
            val = _value_for(ts.operator, ts.column, ts.expression, rows,
                             report._functions, report._aggregates)
```

`aggregation.py:365` y `:396` (fase B / deferred — mismos threading):
```python
    # ... (línea 365)
                               report._functions, report._aggregates)
    # ...
    _resolve_deferred(deferred, report._functions, report._aggregates, registry)   # línea 396
```

**Core pattern a modificar** (líneas 277-307) — `_apply_order` debe recibir y re-enviar `functions`; `_sort_key` debe usarlas (CORR-04) y `raise ValueError` en total ausente (CORR-05):
```python
def _apply_order(spec, children):
    if spec.order_by:
        ob = spec.order_by
        reverse = ob.get("direction") == "desc"
        children = sorted(children, key=lambda c: _sort_key(c, ob), reverse=reverse)   # ← pasar functions
    if spec.suppress_zero:
        sz = spec.suppress_zero
        children = [c for c in children if not _is_zero(c, sz)]
    if spec.top_n is not None:
        children = children[: spec.top_n]
    return children


def _sort_key(child, ob):
    total = ob.get("total")
    expression = ob.get("expression")
    column = ob.get("column")
    if total:
        for t in getattr(child, "totals", []):
            if t.name == total:
                return t.value
        return None                                          # ← BUG CORR-05: devuelve None → TypeError crudo
    if expression:
        return evaluate(expression, getattr(child, "_first_row", {}), {})   # ← BUG CORR-04: pasa {}
    if column:
        if isinstance(child, Group):
            return child.key.get(column) if child.key else None
        if isinstance(child, Detail):
            return child.row.get(column)
        return None
    return 0
```

**Reemplazo verificado por research** (Research §Code Examples 3, líneas 318-341):
```python
def _apply_order(spec, children, functions):
    if spec.order_by:
        ob = spec.order_by
        reverse = ob.get("direction") == "desc"
        children = sorted(children, key=lambda c: _sort_key(c, ob, functions), reverse=reverse)
    if spec.suppress_zero:
        sz = spec.suppress_zero
        children = [c for c in children if not _is_zero(c, sz)]
    if spec.top_n is not None:
        children = children[: spec.top_n]
    return children


def _sort_key(child, ob, functions):
    total = ob.get("total")
    expression = ob.get("expression")
    column = ob.get("column")
    if total:
        for t in getattr(child, "totals", []):
            if t.name == total:
                return t.value
        child_desc = getattr(child, "name", None) or getattr(child, "key", None)
        raise ValueError(f"total de orden inexistente: {total!r} (hijo {child_desc!r})")
    if expression:
        return evaluate(expression, getattr(child, "_first_row", {}), functions)   # era {}
    if column:
        if isinstance(child, Group):
            return child.key.get(column) if child.key else None
        if isinstance(child, Detail):
            return child.row.get(column)
        return None
    return 0
```

**Call site único** (línea 260, dentro de `_build_instance` que ya recibe `report`):
```python
    # fase C sobre los hijos (grupos/detalle), antes de añadir chart/pivot
    node.children = _apply_order(spec, node.children, report._functions)
```

**Firma del evaluador** (referencia, `expressions.py:54-60`) — `functions` es el tercer parámetro opcional:
```python
def evaluate(expr: str, row: dict, functions: dict | None = None) -> Any:
    """Evalúa `expr` sobre `row` y las funciones extra (fusionadas con `_FUNCTIONS`)."""
    merged = {**_FUNCTIONS, **(functions or {})}
    tree = ast.parse(expr, mode="eval")
```

**Error-handling pattern** (convención proyecto: `ValueError` en español con `!r`) — referencia `aggregation.py:45`:
```python
    raise ValueError(f"operador desconocido: {operator!r}")
```

**NOT tocar** — `Section.order_by` (`section.py:117-138`) solo almacena el dict en `GroupSpec.order_by`; `evaluate` ya está importado en `aggregation.py:7`:
```python
        self._spec.order_by = {
            "column": column,
            "direction": direction.lower(),
            "total": total,
            "expression": expression,
        }
```

---

### `pyproject.toml` (config) — DEP-01

**Analog:** self. Eliminar la línea 33 del bloque `dependencies` (32-35); `pydantic>=2` permanece como única dependencia runtime:
```toml
dependencies = [
    "encino-orm>=0.2.1",     # ← ELIMINAR (línea 33, DEP-01)
    "pydantic>=2",
]
```

---

### `uv.lock` (config, regenerado por herramienta) — DEP-01

**Analog:** n/a — regenerar con `uv lock && uv sync`. Verificación: `git diff uv.lock` debe podar exactamente `encino-orm`, `aiomysql`, `aiosqlite`, `asyncpg`, `async-timeout`, `pymysql` + el `requires-dist` de `encino-rpt` (Research Pitfall 6). No editar a mano.

---

### `tests/test_report.py` (test) — CORR-04 / CORR-05

**Analog:** `test_order_top_suppress` (182-195) para el patrón de armado de reporte con `order_by(total=...)`; `test_expression_rejects_unsafe` (32-38) para el patrón `pytest.raises`.

**Imports pattern** (líneas 1-4) — intacto; ya importa pytest, Report y el evaluador:
```python
import pytest

from encino_rpt import Chart, Detail, Pivot, Report, ReportResult
from encino_rpt.expressions import ExpressionError, evaluate
```

**Patrón de test order_by existente a extender** (`test_order_top_suppress`, líneas 182-195):
```python
def test_order_top_suppress():
    rows = [
        {"agente": "Ana", "total": 100},
        {"agente": "Bob", "total": 300},
        {"agente": "Cid", "total": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").total("sum", "total", name="total_agt")
    rep.group("global")
    rep.section("global").order_by(total="total_agt", direction="desc").top(2)
    result = rep.run()

    assert [c.key["agente"] for c in result.root.children] == ["Bob", "Cid"]
```

**Patrón `add_function`** (registro de función custom para CORR-04; `report.py:42-53`):
```python
    def add_function(self, name: str, fn) -> Report:
        """Registra una función de expresión (por renglón)."""
        self._functions[name] = fn
        return self
```

**Patrón `pytest.raises` para CORR-05** (test_report.py:32-38, estilo existente; el match exacto es `match="total de orden inexistente"`):
```python
    with pytest.raises(ExpressionError):
        evaluate("__import__('os')", {})
```

---

### `tests/test_report_renderers.py` (test) — CORR-02

**Analog:** `test_format_value_currency` (8-11), `test_format_value_percent` (14-16), `test_format_value_number` (19-22).

**Imports pattern** (líneas 1-5) — intacto:
```python
import pytest

from encino_rpt import Report
from encino_rpt.models import Format
from encino_rpt.renderers._format import format_value
```

**Patrón de asserts directos a extender** (líneas 8-22) — nuevos tests CORR-02 siguen el mismo estilo `assert format_value(...) == ...`:
```python
def test_format_value_percent():
    fmt = Format(kind="percent", decimals=1, percent_scale=True)
    assert format_value(0.256, fmt) == "25.6%"


def test_format_value_number():
    assert format_value(1.234, Format(decimals=2)) == "1.23"
    assert format_value(None, Format()) == ""
    assert format_value(5, None) == "5"
```

**Casos nuevos esperados** (Research §Validation Architecture/CORR-02): `format_value(1234567.89, Format()) == "1234567.89"`; con `thousands=True` → `"1,234,567.89"`; `0.07` percent → `"7%"`; `0.29` → `"29%"`; `0.256` → `"25.6%"`; sci en extremos `'1e+16'`/`'1e-05'`; test que documente `2.0` → `"2.0"` como intencional (Pitfall 3).

---

### `tests/test_security.py` (test) — SEC-02

**Analog:** `test_csv_formula_injection` (9-15) y `test_excel_formula_injection` (18-27).

**Imports pattern** (líneas 1-5) — intacto:
```python
import pytest

from encino_rpt import Report
from encino_rpt.expressions import ExpressionError, evaluate
from encino_rpt.template import render
```

**Banner pattern** (test_security.py:8) — los nuevos tests SEC-02 llevan banner `# --- P5: inyección de fórmulas con espacio/BOM ---` (convención TESTING.md), siguiendo el patrón P1/P2/P3/P4:
```python
# --- P1: inyección de fórmulas ---
```

**Patrón CSV existente a extender** (líneas 9-15):
```python
def test_csv_formula_injection():
    rows = [{"sku": "=1+1", "cantidad": 2}]
    rep = Report(rows)
    rep.detail("sku", "cantidad")
    result = rep.run()
    out = result.to_csv()
    assert "'=1+1,2" in out
```

**Patrón Excel con importorskip** (líneas 18-27) — los tests SEC-02 Excel usan `pytest.importorskip("openpyxl")` + check de `data_type == "s"`:
```python
def test_excel_formula_injection():
    pytest.importorskip("openpyxl")
    rows = [{"sku": "=1+1"}]
    rep = Report(rows)
    rep.detail("sku")
    result = rep.run()
    ws = result.to_excel()
    cell = ws["A2"]
    assert cell.value == "=1+1"
    assert cell.data_type == "s"
```

**Casos nuevos esperados** (Research §Code Examples 2): `sanitize_csv(" =1+1") == "' =1+1"` (valor original verbatim); `sanitize_csv("\ufeff@evil") == "'\ufeff@evil"`; `is_dangerous('\x0c=1+1') == True`; `is_dangerous('normal') == False`; Excel `data_type == "s"` para espacio/BOM.

---

### `docs/security.md` (docs) — SEC-02 / DEP-01

**Analog:** self. Actualizar la sección "Protección contra inyección de fórmulas" (líneas 30-41) para describir la detección post-recorte de whitespace/BOM:
```markdown
## Protección contra inyección de fórmulas (Excel/CSV)

Los renderers de Excel y CSV neutralizan celdas cuyo valor empieza con
`=`, `+`, `-`, `@`, tabulador o retorno de carro, para que Excel/Calc no las
interprete como fórmulas:

- **CSV**: se prefija una comilla simple (`'`).
- **Excel**: se fuerza el tipo de celda a texto (`data_type = "s"`).

Esto aplica a celdas de detalle, encabezados/pies, pivotes, gráficos y KPIs.
Los totales se calculan en Python (no por fórmula), por lo que no se ven
afectados.
```

---

### `README.md` + `docs/index.md` (docs) — DEP-01

**Analog:** self. Re-fraseo neutro opcional de la línea 4 de cada archivo (Open Question 1 / Assumption A3):

`README.md:4` y `docs/index.md:4` hoy dicen:
```markdown
(la salida de `fetch_all` / `fetch_many` / `paginate`) en un **árbol canónico**
```
Re-fraseo propuesto: `(la salida de consultas ya materializadas como `list[dict]`) en un **árbol canónico**`. No editar `.planning/codebase/*.md` ni `AGENTS.md` (snapshots GSD — se regeneran, no se editan a mano).

---

## Shared Patterns

### Patrón 1: Threading de funciones del reporte (CORR-04)
**Source:** `encino_rpt/aggregation.py:102,174,266,270,365,396`
**Apply to:** `_apply_order`/`_sort_key` (`aggregation.py:277-307`) y su call site (línea 260)
```python
report._functions, report._aggregates   # patrón canónico en 5 sitios; _sort_key era el único divergente con {}
```
`report` ya está disponible en `_build_instance` (parámetro, línea 234); el threading es solo firmas + call site.

### Patrón 2: Errores en español con `!r` (CORR-05)
**Source:** `encino_rpt/aggregation.py:45`, `encino_rpt/report.py:247-248`, `encino_rpt/expressions.py:73`
**Apply to:** branch `total` de `_sort_key`
```python
raise ValueError(f"total de orden inexistente: {total!r} (hijo {child_desc!r})")
```
Convención: `ValueError` para config inválida, mensaje en español, valor ofensor vía `!r`. Nunca fallback silencioso (CONTEXT §code_context).

### Patrón 3: Escala percent exacta con Decimal (CORR-02)
**Source:** `encino_rpt/renderers/_format.py:6` (`from decimal import Decimal` ya presente)
**Apply to:** branch `percent_scale` con `decimals=None`
```python
d = (Decimal(str(abs(value))) * 100).normalize()
text = format(d, "f")
```
Anti-patrón: `str(0.07 * 100)` → `'7.000000000000001'` (regresión verificada, Research Pitfall 1).

### Patrón 4: Fuente única de verdad del sanitizer (SEC-02)
**Source:** `encino_rpt/renderers/_sanitize.py:8-10`
**Apply to:** solo `is_dangerous`; `sanitize_csv` (13-17) y `write_excel_cell` (20-27) consumidores sin cambios
```python
_LEADING_TRIM = re.compile(r"^[\s\ufeff]+")
return isinstance(value, str) and _LEADING_TRIM.sub("", value).startswith(_DANGEROUS_PREFIXES)
```
Anti-patrón: `value.lstrip()` solo NO recorta BOM (`'\ufeff'.isspace() == False`, verificado) y duplicar el check en cada renderer.

### Patrón 5: Banner de sección + `importorskip` en tests de seguridad
**Source:** `tests/test_security.py:8,19`
**Apply to:** nuevos tests SEC-02
```python
# --- P5: inyección de fórmulas con espacio/BOM ---
pytest.importorskip("openpyxl")   # guard para extras opcionales
```
Convención TESTING.md: sin fixtures; asserts directos sobre `to_csv()`/`to_excel()` output.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `uv.lock` | config | n/a | Regenerado por `uv lock`; no es editable a mano; verificación vía `git diff` (Pitfall 6). |

## Metadata

**Analog search scope:** `encino_rpt/` (todos los módulos), `tests/` (3 archivos), `pyproject.toml`, `docs/security.md`, `README.md`, `docs/index.md`
**Files scanned:** 24 (18 módulos + 3 tests + 3 config/docs)
**Pattern extraction date:** 2026-09-16
**Nota:** Fase de corrección sobre código existente — no hay archivos nuevos; todos los analongs son self-analogs con patrones de referencia intra-módulo. Los reemplazos exactos vienen del Research (probes verificadas) y están citados con sus números de línea.