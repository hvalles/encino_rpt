# Coding Conventions

**Analysis Date:** 2026-09-17

## Naming Patterns

**Modules (files):**
- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`
- Leading underscore for internal modules: `encino_rpt/_specs.py` (builder dataclasses), `encino_rpt/renderers/_format.py`, `encino_rpt/renderers/_sanitize.py`, `encino_rpt/renderers/_walk.py`
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_perf_smoke.py`

**Classes:**
- `PascalCase`: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`, `FieldSpec`, `ExpressionError`, `AggregationError`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)
- Internal helper class `_PathNode` (trie node) prefixed `_` (`encino_rpt/aggregation.py:246`)

**Functions:**
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`, `build_pivot`, `render`, `build`, `walk`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_wrap`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_make_path_node`, `_walk`, `_full_row`, `_total_row`, `_cell_attrs`, `_style_attr`, `_add_thousands`
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the only cross-module abbreviations

**Variables:**
- `snake_case`: `rows`, `visible_set`, `child_pairs`, `deferred`, `registry`, `children_map`, `root_spec`, `spec`
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._groups`, `self._fields`, `self._detail`, `self._order`, `self._formats`, `self._styles`, `self._datasets`, `self._kpis`, `self._aggregates` (`encino_rpt/report.py:29-41`), `self._spec` (`encino_rpt/section.py:11-12`)
- Pydantic `PrivateAttr` for non-serialized context: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:124-126`)
- Instance-private attributes set transiently by `ExcelRenderer.render` (not in `__init__`): `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:55-58`)

**Constants:**
- `UPPER_SNAKE`, module-level: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:46-48`), `_TOKEN` regex (`encino_rpt/template.py:7`), `_DANGEROUS_PREFIXES`, `_LEADING_TRIM` (`encino_rpt/renderers/_sanitize.py:7-9`), `_SAFE_PROP`, `_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:21-22`), `SCHEMA_VERSION = "1.0"` (`encino_rpt/renderers/json.py:7`)

**Type hints:**
- `from __future__ import annotations` at the top of every module (enables PEP 604 unions and builtin generics)
- Prefer `str | None` over `Optional[str]`; builtin generics (`list[dict]`, `dict[str, Any]`) everywhere
- `Any` used for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`

## Code Style

**Formatting:**
- **ruff** `0.16.7` — formatter is now configured via `[tool.ruff.format]` in `pyproject.toml:78-79` with `quote-style = "double"`
- `[tool.ruff]` config (`pyproject.toml:73-76`): `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`
- Line length is 88 (enforced by ruff format check in CI, `.github/workflows/ci.yml:50`)
- Indentation: 4 spaces throughout
- Double quotes for strings (ruff format `quote-style = "double"`)

**Linting:**
- **ruff** `0.16.7` (dev dependency, `pyproject.toml:53`), run with defaults: `uv run ruff check` (`.github/workflows/ci.yml:30`). No `select`/`ignore` pinned — ruff defaults only.

**Type checking:**
- **mypy** `2.3.1` (dev dependency, `pyproject.toml:54`), configured in `[tool.mypy]` (`pyproject.toml:63-71`):
  - `plugins = ["pydantic.mypy"]`
  - `python_version = "3.10"`
  - `check_untyped_defs = true`
  - `warn_unused_ignores = true`
  - `warn_redundant_casts = true`
  - `no_implicit_optional = true`
  - `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs)
- Run in CI as `uv run mypy encino_rpt` (`.github/workflows/ci.yml:47`)

## Import Organization

**Order (top to bottom):**
1. `from __future__ import annotations` (always first)
2. stdlib imports (`ast`, `operator`, `csv`, `io`, `re`, `typing`, `collections.abc`, `datetime`, `decimal`, `html`, `time`)
3. blank line, then relative imports grouped alphabetically

**Examples:**
- `encino_rpt/models.py:3-7`: future import → `typing` (stdlib) → `pydantic`
- `encino_rpt/aggregation.py:3-24`: future import → `typing` → blank → relative imports grouped alphabetically (`_specs`, `charts`, `expressions`, `models`, `pivot`, `template`)
- `from ._specs import FieldSpec, GroupSpec, KpiSpec` (`encino_rpt/report.py:7`)
- `from ..models import Image, Link` (`encino_rpt/renderers/csv.py:8`)
- `from ._walk import walk` (`encino_rpt/renderers/csv.py:11`)

**Path aliases:** none — only relative imports are used.

**Lazy imports (inside methods, not module top):**
- `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:367`)
- `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html` (`encino_rpt/models.py:162`); same pattern for csv/text/excel/json/pdf (`models.py:175,185,200,213,227`)
- `from openpyxl import Workbook` + `from openpyxl.styles import Font` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:44-46`)
- `from reportlab.platypus import ...` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:31-40`)
- Per-helper imports for optional deps: `from openpyxl.styles import Font` inside `_full_row`/`_total_row`/`_apply_conditional`/`_chart`/`_pivot` (`encino_rpt/renderers/excel.py:170,179,197,217,252`); `from reportlab.platypus import Paragraph` inside `pdf.py:125,137,143`

## Error Handling

**Exception hierarchy (all subclasses of `ValueError`):**
- `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:51`)
- `class AggregationError(ValueError)` (`encino_rpt/aggregation.py:30`)

**Error message language: Spanish, always.**

**Validation errors:**
- `ValueError` for invalid config: `raise ValueError("`columns` y `path` son excluyentes")` (`encino_rpt/report.py:324`), `raise ValueError(f"corte ya declarado: {name!r}")` (`report.py:326`)
- `KeyError` for unknown named lookups: `f"corte no declarado: {name!r}"` (`encino_rpt/report.py:358`)
- `IndexError` for out-of-range param access: `f"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:26-28`)
- `ValueError` for invalid direction: `f"dirección de orden inválida: {direction!r}"` (`encino_rpt/section.py:172-173`)

**Context wrapping pattern (`_wrap`):**
- `_wrap(context, fn, *args)` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:34-43`). Used for field enrichment (`campo {name!r} (fila {index})`), totals (`total {name or operator!r} (grupo {spec.name!r})`), deferred totals, and KPIs.

**Optional dependency errors (guarded imports):**
- `raise ImportError("openpyxl no está instalado; instala el extra `excel`") from exc` (`encino_rpt/renderers/excel.py:47-50`)
- `raise ImportError("reportlab no está instalado; instala el extra `pdf`") from exc` (`encino_rpt/renderers/pdf.py:41-44`)
- Both branches marked `# pragma: no cover - depende del entorno` (excluded from coverage via `exclude_lines` in `pyproject.toml:88`)

**Aggregation never catches exceptions:** a failing expression propagates up through `run()` to the caller. `AggregationError` passes through `_wrap` unchanged (re-raised, not double-wrapped).

## Logging

No logging framework used — the library is pure and stateless, so no `logging` module anywhere. Errors are raised, not logged.

## Comments

**Docstrings:**
- One-line module docstring in every module (Spanish): `"""Builder fluido `Report`."""` (`encino_rpt/report.py:1`), `"""Evaluador seguro de expresiones (sin `eval`, whitelist vía `ast`)."""` (`encino_rpt/expressions.py:1`)
- Google-style docstrings (Spanish) on every public class and method, with `Args:`, `Returns:`, `Raises:` sections — see `Report.group` (`encino_rpt/report.py:295-322`), `ReportResult.to_excel` (`encino_rpt/models.py:189-202`), `Report.set_format` (`report.py:70-98`)
- Renderer `render()` docstrings include a `Raises:` section documenting the `ImportError` for optional deps (`excel.py:41-42`, `pdf.py:28-29`)

**Section banner comments** inside longer modules:
- `# --- funciones / campos ---` (`encino_rpt/report.py:43`)
- `# --- detalle / grupos ---` (`report.py:281`)
- `# --- árbol de grupos ---` (`encino_rpt/aggregation.py:155`)
- `# --- fase B ---` (`aggregation.py:447`)
- `# --- plantillas (fase final) ---` (`aggregation.py:464`)
- `# --- P1: inyección de fórmulas ---` and similar in `tests/test_security.py`

**Inline comments** explain non-obvious invariants, in Spanish:
- `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:80`)
- `# children: subgrupos o detalle` (`encino_rpt/aggregation.py:324`)
- `# Contexto interno (no serializado)...` (`encino_rpt/models.py:123`)
- `# fase C sobre los hijos (grupos/detalle), antes de añadir chart/pivot` (`aggregation.py:349`)
- `# dividir cada fila una sola vez (PERF-02)` (`aggregation.py:260`)

**Comments in source are Spanish.** Avoid English comments in new code.

## Function Design

**Signature conventions:**
- Keyword-only parameters after `*` for optional config: `def set_format(self, column: str, *, kind: str = "number", ...)` (`encino_rpt/report.py:70-82`), `def add_field(self, name: str, expression: str | None = None, *, after: str | None = None, ...)` (`report.py:173-183`)
- Optional config params often untyped (`format=None`, `fn`) where the type is `Format`/callable — see `add_function(self, name: str, fn) -> Report` (`report.py:44`)
- Fluent builder methods always return `self` (or `Section`) for chaining, with `Returns:` docstring noting "El propio reporte (fluido)."

**Size:** functions are short and single-purpose; long module bodies are split into private `_`-prefixed helpers (`aggregation.py` is the longest at 566 lines but decomposed into ~20 helpers).

**Return values:** renderers return strings (`csv.py`, `html.py`, `text.py`, `json.py`), bytes (`pdf.py`), or a worksheet (`excel.py`); `format_value` returns `str`; `evaluate` returns `Any`.

## Module Design

**Exports:**
- `encino_rpt/__init__.py` re-exports 14 public names via `__all__` (`__init__.py:20-34`). `Section` is intentionally NOT exported (reachable only via `Report.group()`/`Report.section()`).
- `encino_rpt/renderers/__init__.py` exports the 6 renderer classes via `__all__` (`renderers/__init__.py:10-17`).

**Barrel files:** `encino_rpt/__init__.py` and `encino_rpt/renderers/__init__.py` are the only barrels; internal helpers (`_specs.py`, `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `aggregation.py`) are imported directly by path, not re-exported.

**Module responsibilities:**
- `encino_rpt/models.py` — pydantic `BaseModel` canonical tree (13 models), `Field(default_factory=...)` for mutable defaults, `PrivateAttr` for non-serialized context, recursive `Group.children` resolved with `Group.model_rebuild()` at module bottom (`models.py:232`)
- `encino_rpt/_specs.py` — internal `@dataclass` specs, `field(default_factory=list)` for mutable defaults
- `encino_rpt/aggregation.py` — the engine (enrich, group tree, totals, deferred resolution, templates, KPIs)
- `encino_rpt/renderers/` — visitor-style renderers consuming the shared `walk()` generator

## Patterns to Follow

- **Fluent builder**: validate immediately (raise early) and return `self`
- **"Truthiness coalescing" for label fallbacks**: `label = t.label or t.name or t.operator` (`encino_rpt/renderers/csv.py:55`, also `text.py:46`, `html.py:71`, `pdf.py:96`, `excel.py:107`)
- **Dict `or` fallback for user config**: `self.classes = classes or {}`, `self.styles = styles or {}`, `spec.options or {}`
- **Module-level `_OPS`-style dispatch dicts** instead of if/else chains for operator lookup: `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`encino_rpt/expressions.py:10-42`), `_OPS` (`renderers/html.py:12-19`), `_COLOR_OPS` (`renderers/excel.py:10-17`)
- **Preserve insertion order explicitly** where dicts don't: `_ordered_unique` (`encino_rpt/pivot.py:49-56`), `order` list parallel to `index` dict in `_partition` (`encino_rpt/aggregation.py:178-189`)
- **Pydantic recursive model** resolved with `Group.model_rebuild()` (`encino_rpt/models.py:232`)
- **JSON versioning**: `JsonRenderer.to_dict` injects `schema_version` via `{"schema_version": SCHEMA_VERSION, **result.model_dump(mode="json")}` (`encino_rpt/renderers/json.py:27`)

---

*Convention analysis: 2026-09-17*
