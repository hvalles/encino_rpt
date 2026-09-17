# Coding Conventions

**Analysis Date:** 2026-09-17

## Naming Patterns

**Files (modules):**
- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`
- Leading-underscore for internal modules: `_specs.py` (builder dataclasses), `renderers/_format.py`, `renderers/_sanitize.py`, `renderers/_walk.py` (shared traversal)
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`

**Classes:**
- `PascalCase`: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`, `FieldSpec`, `ExpressionError`, `AggregationError`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)

**Functions:**
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`, `build_pivot`, `render`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_wrap`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_make_path_node`
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the only cross-module abbreviations

**Variables:**
- `snake_case`: `rows`, `visible_set`, `child_pairs`, `deferred`, `registry`, `children_map`
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._groups` (`encino_rpt/report.py:27-39`), `self._spec` (`encino_rpt/section.py:11-12`)
- Pydantic `PrivateAttr` for non-serialized context: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:124-126`)
- Instance-private attributes set transiently by `ExcelRenderer.render` (not in `__init__`): `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:51-54`)

**Constants:**
- `UPPER_SNAKE`, module-level, usually private: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:45-47`), `_TOKEN` regex (`encino_rpt/template.py:7`), `_DANGEROUS_PREFIXES`, `_LEADING_TRIM` (`encino_rpt/renderers/_sanitize.py:7-9`), `_SAFE_PROP`, `_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:21-22`), `SCHEMA_VERSION = "1.0"` (`encino_rpt/renderers/json.py:7`)
- Private module-level dispatch dicts map operator/type keys to lambdas: `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`encino_rpt/expressions.py:9-42`), `_OPS` (`encino_rpt/renderers/html.py:12-19`), `_COLOR_OPS` (`encino_rpt/renderers/excel.py:10-17`)

**Types:**
- Prefer `str | None` over `Optional[str]`; PEP 604 unions and builtin generics (`list[dict]`, `dict[str, Any]`) everywhere, enabled by `from __future__ import annotations`
- `Any` used for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`

## Code Style

**Formatting:**
- No formatter configured — no `black`, no `ruff format`. There is **no ruff config** (`pyproject.toml` has no `[tool.ruff]`, no `ruff.toml`/`.ruff.toml`).
- Linting only: **ruff** `0.16.7` (dev dependency, `pyproject.toml:53`), run with defaults via `uv run ruff check` (`.github/workflows/ci.yml:29-30`).
- Only rule set: ruff defaults. No `select`/`ignore` pinned. The suite is currently clean (`ruff check` exits 0).
- Indentation: 4 spaces throughout. Line length is not enforced.
- One known outlier: `encino_rpt/__init__.py:3-17` aligns `from .models import (...)` items to column 21, inconsistent with `encino_rpt/renderers/__init__.py` which uses one-item-per-line at 4-space indent.

## Import Organization

**Order** (every module follows this):
1. `from __future__ import annotations` (first line after the module docstring)
2. blank line
3. stdlib imports
4. blank line
5. third-party imports (only `pydantic` in `models.py`; `openpyxl`/`reportlab` imported lazily inside methods)
6. blank line
7. relative imports (`from .`, `from ..`)

Examples:
- `encino_rpt/models.py:3-7`: future import → `typing` (stdlib) → `pydantic`
- `encino_rpt/aggregation.py:3-20`: future import → blank → relative imports grouped alphabetically

**No path aliases.** All intra-package imports are always relative:
- `from ._specs import ...` (`encino_rpt/report.py:7`)
- `from ..models import ...` (`encino_rpt/renderers/csv.py:8`)
- `from ._walk import walk` (`encino_rpt/renderers/csv.py:11`)

**Lazy imports for cycles and optional deps** (import inside the method, never at module top):
- `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:286`)
- `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html` (`encino_rpt/models.py:160`)
- `from openpyxl import Workbook` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:42-44`)
- `from reportlab.platypus import ...` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:30-39`)
- Per-helper imports: `from openpyxl.styles import Font` inside `_full_row`/`_total_row`/`_apply_conditional` (`encino_rpt/renderers/excel.py:161,170,188`)

## Error Handling

**Domain exceptions subclass builtins** (not `Exception` directly):
- `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:50`)
- `class AggregationError(ValueError)` (`encino_rpt/aggregation.py:23`)

**Messages in Spanish, always include the offending value via `!r`:**
- `ValueError` for invalid config: `raise ValueError(f"corte ya declarado: {name!r}")` (`encino_rpt/report.py:250`)
- `KeyError` for unknown named lookups: `f"corte no declarado: {name!r}"` (`encino_rpt/report.py:277`)
- `IndexError` for out-of-range param access: `f"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:26`)
- `AggregationError` wraps engine failures with context: `f"total {ts.name or ts.operator!r} (grupo {spec.name!r})"` (`encino_rpt/aggregation.py:195`)

**Context wrapping pattern** (`encino_rpt/aggregation.py:27-36`): `_wrap(context, fn, *args)` re-raises any error as `AggregationError` with a readable context string, preserving `AggregationError` as-is and chaining via `from exc`. Use this for any engine-level failure.

**Optional-dependency guards** re-raise `ImportError` with `from exc` and a Spanish install hint:
- `raise ImportError("openpyxl no está instalado; instala el extra `excel`") from exc` (`encino_rpt/renderers/excel.py:46`)
- `raise ImportError("reportlab no está instalado; instala el extra `pdf`") from exc` (`encino_rpt/renderers/pdf.py:41`)
- Both guarded with `# pragma: no cover - depende del entorno` (`excel.py:45`, `pdf.py:40`)

**Builder validates eagerly** (raise early, not at `run()`): `group()` raises `ValueError` when `columns` and `path` are both set (`encino_rpt/report.py:247-248`); `Section.order_by` raises for invalid direction (`encino_rpt/section.py:130-131`). Cross-reference validation (`source`/`parent`/`custom:` declared) happens in `_validate` at `run()` (`encino_rpt/aggregation.py:441-458`).

**Aggregation never catches its own exceptions** — a failing expression propagates up through `run()` to the caller (wrapped as `AggregationError`).

## Logging

- No logging framework used — the library is pure and stateless, so no `logging` module anywhere. Errors are raised, not logged.

## Comments

- Module docstring in every module (one line, Spanish): `"""Agregación: enriquece renglones, construye el árbol de grupos y resuelve totales."""` (`encino_rpt/aggregation.py:1`)
- Google-style docstrings (Spanish) on every public class and method with `Args:`, `Returns:`, `Raises:` sections — see `Report.group` (`encino_rpt/report.py:224-246`) and `ReportResult.to_excel` (`encino_rpt/models.py:187-200`)
- Section banner comments inside longer modules: `# --- funciones / campos ---` (`encino_rpt/report.py:41`), `# --- árbol de grupos ---` (`encino_rpt/aggregation.py:138`), `# --- fase B ---` (`encino_rpt/aggregation.py:381`), `# --- plantillas (fase final) ---` (`encino_rpt/aggregation.py:392`)
- Inline comments explain non-obvious invariants, in Spanish: `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:80`), `# children: subgrupos o detalle` (`encino_rpt/aggregation.py:288`), `# Contexto interno (no serializado)...` (`encino_rpt/models.py:123`)
- Comments in source are **Spanish**; avoid English comments in new code.

## Function Design

**Fluent builder methods** return `self` typed as the class: `-> Report` (`encino_rpt/report.py:42,55,68,...`), `-> Section` (`encino_rpt/section.py:14,26,40,...`). They validate immediately and return `self` for chaining.

**Keyword-only args after the first positional(s), marked `*`:**
- `def set_format(self, column: str, *, kind: str = "number", ...)` (`encino_rpt/report.py:68-72`)
- `def add_field(self, name: str, expression: str | None = None, *, after: str | None = None, ...)` (`encino_rpt/report.py:145-148`)

**Optional params default to `None`** and are stored/checked explicitly: `columns: str | None = None`, `title: str | None = None`, `source: str | None = None`.

**`format=None`** is the one place a shadowed builtin name is used as a parameter (avoids importing `Format` in the public builder API) — `encino_rpt/report.py:127`, `encino_rpt/section.py:43`.

**Render methods return plain data:** `str` (`render_html`, `to_csv`, `to_text`, `to_json`), `Worksheet` (`to_excel`), `bytes` (`to_pdf`) — `encino_rpt/models.py:150-227`.

**Use `row.get(col)` with `None` fallbacks, never `row[col]`** — see `_value_for` (`encino_rpt/aggregation.py:80`), `_partition` (`encino_rpt/aggregation.py:167`), all renderers.

## Module Design

**Public API surface** is defined in `encino_rpt/__init__.py` with an explicit `__all__` (14 names). `Section` is intentionally **not** exported — it is reachable only via `Report.group()` / `Report.section()` return values.

**`encino_rpt/renderers/__init__.py`** re-exports all six renderers with `__all__ = ["CsvRenderer", "ExcelRenderer", "HtmlRenderer", "JsonRenderer", "PdfRenderer", "TextRenderer"]`.

**Internal modules are not exported:** `_specs.py`, `aggregation.py`, `expressions.py`, `template.py`, `pivot.py`, `charts.py`, `renderers/_format.py`, `renderers/_sanitize.py`, `renderers/_walk.py`.

**Layered design:**
- Public fluent facade: `encino_rpt/report.py` (`Report`) + `encino_rpt/section.py` (`Section`) — mutate internal spec dataclasses
- Internal specs: `encino_rpt/_specs.py` (dataclasses, `field(default_factory=list)` for mutable defaults)
- Canonical output model: `encino_rpt/models.py` (pydantic `BaseModel`, `Field(default_factory=...)` for mutable defaults, `PrivateAttr` for non-serialized context)
- Pipeline: `encino_rpt/aggregation.py` → `charts.py` / `pivot.py` / `expressions.py` / `template.py`
- Renderers: `encino_rpt/renderers/` — consume the shared `walk` generator and dispatch per event

**Shared tree traversal:** `encino_rpt/renderers/_walk.py` exports a single iterative generator `walk(root)` that yields typed events `("group_start"|"group_end"|"detail"|"chart"|"pivot", node)`. Every renderer imports `walk` and implements a thin `_walk`/`_collect` method that dispatches on `event`. Do NOT reimplement tree recursion per renderer — always `from ._walk import walk`.

**Known coupling:** `aggregation.py` reaches into `Report` private attributes directly — `report._rows`, `report._datasets`, `report._fields`, `report._functions`, `report._groups`, `report._order`, `report._aggregates`, `report._kpis`, `report._title`, `report._params` (`encino_rpt/aggregation.py:110,115,128,140-152,197,424`). Prefer adding accessor methods on `Report` if this coupling grows.

## Patterns to Follow

- **Fluent builder**: validate immediately (raise early) and return `self`
- **"Truthiness coalescing" for label fallbacks**: `label = t.label or t.name or t.operator` (`encino_rpt/renderers/csv.py:50`, also `text.py:46`, `html.py:69`, `pdf.py:86`, `excel.py:103`)
- **Dict `or` fallback for user config**: `self.classes = classes or {}`, `self.styles = styles or {}`, `spec.options or {}`
- **Module-level `_OPS`-style dispatch dicts** instead of if/else chains for operator lookup
- **Preserve insertion order explicitly** where dicts don't: `_ordered_unique` (`encino_rpt/pivot.py:47-54`), `order` list parallel to `index` dict in `_partition` (`encino_rpt/aggregation.py:164-174`)
- **Pydantic recursive model** resolved with `Group.model_rebuild()` at module bottom (`encino_rpt/models.py:230`)
- **JSON versioning**: `JsonRenderer` injects `schema_version` via `{"schema_version": SCHEMA_VERSION, **result.model_dump(mode="json")}` (`encino_rpt/renderers/json.py:27`)

## Anti-Patterns

### Reimplementing tree traversal per renderer
**What happens:** Each renderer once carried its own recursive `_walk` visitor with duplicated dispatch logic.
**Why it's wrong:** Divergent traversal order and duplicated recursion (which blows the stack on deep `path` hierarchies).
**Do this instead:** Import the shared iterative generator `from ._walk import walk` and dispatch on its typed events (see `encino_rpt/renderers/csv.py:43-66`).

### `.__init__.py` import-list alignment
**What happens:** `encino_rpt/__init__.py` pads `from .models import (...)` items to align at column 21.
**Why it's wrong:** Inconsistent with every other module (4-space indent, one item per line).
**Do this instead:** One-item-per-line at 4-space indent, matching `encino_rpt/renderers/__init__.py`.

### Cross-module private attribute access
**What happens:** `aggregation.py` reads `report._rows`, `report._groups`, `report._order`, etc. directly.
**Why it's wrong:** Tightly couples the engine to the builder's private state; a rename silently breaks aggregation.
**Do this instead:** Add accessor methods on `Report` and have `aggregation.py` call those if the coupling grows.

### Duplicated operator/conditional tables per renderer
**What happens:** `_OPS` (HTML) and `_COLOR_OPS` (Excel) define the same six comparison lambdas independently.
**Why it's wrong:** Drift risk if a new operator (`eq`, `ne`, etc.) is added in only one place.
**Do this instead:** Extract a shared `_compare(when, a, b)` helper if another renderer needs the same table.
