# Coding Conventions

**Analysis Date:** 2026-09-17

## Naming Patterns

**Files:**
- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`, `readers.py`
- Leading underscore for internal modules: `encino_rpt/_specs.py`, `encino_rpt/renderers/_format.py`, `encino_rpt/renderers/_sanitize.py`, `encino_rpt/renderers/_walk.py`
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_readers.py`, `test_perf_smoke.py`

**Classes:**
- `PascalCase`: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`, `Reader`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `MarkdownRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)
- Internal reader classes: `_DelimitedReader`, `JsonReader`, `JsonLinesReader`, `TuplesReader`, `ExcelReader` (`encino_rpt/readers.py`)
- Internal helper class `_PathNode` (trie node) prefixed `_` (`encino_rpt/aggregation.py:246`)

**Functions:**
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`, `build_pivot`, `render`, `build`, `walk`, `_coerce`, `register_reader`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_wrap`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_make_path_node`, `_walk`, `_full_row`, `_total_row`, `_cell_attrs`, `_style_attr`, `_add_thousands`, `_md_escape`, `_md_url`, `_md_cell`, `_md_table`
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the only cross-module abbreviations

**Variables:**
- `snake_case`: `rows`, `visible_set`, `child_pairs`, `deferred`, `registry`, `children_map`, `root_spec`, `spec`
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._groups`, `self._fields`, `self._detail`, `self._order`, `self._formats`, `self._styles`, `self._datasets`, `self._kpis`, `self._aggregates` (`encino_rpt/report.py:29-41`), `self._spec` (`encino_rpt/section.py:11-12`), `self._delimiter` (`encino_rpt/readers.py:165`)

**Types:**
- Pydantic `PrivateAttr` for non-serialized context: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:124-126`)
- Instance-private attributes set transiently by `ExcelRenderer.render` (not in `__init__`): `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:55-58`)

**Constants:**
- `UPPER_SNAKE`, module-level: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:46-48`), `_TOKEN` regex (`encino_rpt/template.py:7`), `_DANGEROUS_PREFIXES`, `_LEADING_TRIM` (`encino_rpt/renderers/_sanitize.py:7-9`), `_SAFE_PROP`, `_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:21-22`), `SCHEMA_VERSION = "1.0"` (`encino_rpt/renderers/json.py:7`), `_READERS` registry (`encino_rpt/readers.py:35`), `_FORMAT_BY_EXT` map (`encino_rpt/readers.py:318-325`)

## Code Style

**Formatting:**
- Tool: `ruff` `0.16.7` (dev dependency, `pyproject.toml:53`)
- `[tool.ruff.format]` (`pyproject.toml:78-79`): `quote-style = "double"`
- `[tool.ruff]` (`pyproject.toml:73-76`): `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`
- Line length is 88 (enforced by `ruff format --check encino_rpt tests` in CI, `.github/workflows/ci.yml:50`)
- Indentation: 4 spaces throughout
- Double quotes for all string literals (ruff format `quote-style = "double"`)

**Linting:**
- Tool: `ruff` `0.16.7`, run with defaults: `uv run ruff check` (`.github/workflows/ci.yml:30`). No `select`/`ignore` pinned — ruff defaults only.
- Type checking: `mypy` `2.3.1` (dev dependency, `pyproject.toml:54`), configured in `[tool.mypy]` (`pyproject.toml:63-71`):
  - `plugins = ["pydantic.mypy"]`
  - `python_version = "3.10"`
  - `check_untyped_defs = true`, `warn_unused_ignores = true`, `warn_redundant_casts = true`, `no_implicit_optional = true`
  - `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs)
  - Run in CI as `uv run mypy encino_rpt` (`.github/workflows/ci.yml:47`)

**Type hints:**
- `from __future__ import annotations` at the top of every module (enables PEP 604 unions and builtin generics)
- Prefer `str | None` over `Optional[str]`; builtin generics (`list[dict]`, `dict[str, Any]`) everywhere
- `Any` used for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`
- Optional config params often untyped (`format=None`, `fn`) where the type is `Format`/callable — see `add_function(self, name: str, fn)` (`encino_rpt/report.py:93`)

## Import Organization

**Order:**
1. `from __future__ import annotations`
2. Standard library imports (alphabetical)
3. Third-party imports (`pydantic`, `openpyxl`, `reportlab`)
4. Relative imports (alphabetical)

Examples:
- `encino_rpt/models.py:3-7`: future → `typing` (stdlib) → `pydantic`
- `encino_rpt/readers.py:3-10`: future → `csv`, `io`, `json`, `math`, `pathlib`, `typing` (stdlib, alphabetical)
- `encino_rpt/aggregation.py:3-24`: future → `typing` → blank → relative imports grouped alphabetically (`_specs`, `charts`, `expressions`, `models`, `pivot`, `template`)

**Path Aliases:**
- No path aliases configured (no `pytest` `pythonpath` beyond `pythonpath = ["."]` in `pyproject.toml:46`, no `import`-rewriting). Imports use package-relative form: `from ._specs import FieldSpec` (`encino_rpt/report.py:7`), `from ..models import Image, Link` (`encino_rpt/renderers/csv.py:8`)

**Lazy imports (to break cycles and isolate optional deps):**
- `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:419`)
- `from .readers import read as read_rows` inside `Report.read()` (`encino_rpt/report.py:75`)
- `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html` (`encino_rpt/models.py:178`); same pattern for csv/text/excel/json/pdf/markdown (`models.py:235,266,299,327,345,361`)
- `from openpyxl import load_workbook` inside `ExcelReader.read` (`encino_rpt/readers.py:296`)
- `from openpyxl import Workbook` + `from openpyxl.styles import Font` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:44-46`)
- `from reportlab.platypus import ...` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:31-40`)
- Per-helper imports for optional deps: `from openpyxl.styles import Font` inside `_full_row`/`_total_row`/`_apply_conditional`/`_chart`/`_pivot` (`encino_rpt/renderers/excel.py:170,179,197,217,252`); `from reportlab.platypus import Paragraph` inside `pdf.py:125,137,143`

## Error Handling

**Custom exception classes:**
- `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:51`) — subclasses `ValueError`
- `class AggregationError(ValueError)` (`encino_rpt/aggregation.py:30`) — subclasses `ValueError`

**Patterns (all messages in Spanish):**
- `ValueError` for invalid config: `raise ValueError("`columns` y `path` son excluyentes")` (`encino_rpt/report.py:376`), `raise ValueError(f"corte ya declarado: {name!r}")` (`report.py:378`), `raise ValueError("`columns` requerido para reader 'tuples'")` (`encino_rpt/readers.py:265`)
- `KeyError` for unknown named lookups: `f"corte no declarado: {name!r}"` (`encino_rpt/report.py:410`)
- `IndexError` for out-of-range param access: `f"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:26-28`)
- `ValueError` for invalid direction: `f"dirección de orden inválida: {direction!r}"` (`encino_rpt/section.py:163-164`)
- `TypeError` for unsupported sources: `f"fuente no soportada: {type(source).__name__!r}"` (`encino_rpt/readers.py:127`)
- `_wrap(context, fn, *args)` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:34-43`). Used for field enrichment (`campo {name!r} (fila {index})`), totals (`total {name or operator!r} (grupo {spec.name!r})`), deferred totals, and KPIs.
- `raise ImportError("openpyxl no está instalado; instala el extra `excel`") from exc` (`encino_rpt/renderers/excel.py:47-50`, `encino_rpt/readers.py:298-300`)
- `raise ImportError("reportlab no está instalado; instala el extra `pdf`") from exc` (`encino_rpt/renderers/pdf.py:41-44`)
- Both branches marked `# pragma: no cover - depende del entorno` (excluded from coverage via `exclude_lines` in `pyproject.toml:88`)
- Controlled `RecursionError` translation: `JsonRenderer.render`/`to_dict` catch `RecursionError` and re-raise `ValueError` with a clear "demasiado profunda" message (`encino_rpt/renderers/json.py:32-55`)

## Logging

**Framework:** None. No `logging` module usage anywhere in `encino_rpt/`. Errors propagate to the caller as exceptions; there is no internal logging or print-based tracing.

## Comments

**Module docstrings:**
- One-line module docstring in every module (Spanish): `"""Builder fluido `Report`."""` (`encino_rpt/report.py:1`), `"""Evaluador seguro de expresiones (sin `eval`, whitelist vía `ast`)."""` (`encino_rpt/expressions.py:1`), `"""Readers multi-formato para `Report` (CSV, TSV, JSON, JSONL, tuplas, Excel)."""` (`encino_rpt/readers.py:1`)

**Class/method docstrings:**
- Google-style docstrings (Spanish) on every public class and method, with `Args:`, `Returns:`, `Raises:`, and `Yields:` sections — see `Report.group` (`encino_rpt/report.py:347-374`), `ReportResult.to_excel` (`encino_rpt/models.py:317-329`), `ReportResult.iter_html` (`encino_rpt/models.py:192-222`), `readers.read` (`encino_rpt/readers.py:350-371`)

**Section markers:**
- `# --- funciones / campos ---` (`encino_rpt/report.py:92`)
- `# --- detalle / grupos ---` (`report.py:330`)
- `# --- árbol de grupos ---` (`encino_rpt/aggregation.py:155`)
- `# --- fase B ---` (`aggregation.py:447`)
- `# --- plantillas (fase final) ---` (`aggregation.py:464`)
- `# --- P1: inyección de fórmulas ---` and similar in `tests/test_security.py`
- `# --- auto-detección de tipos (_coerce) ---` in `tests/test_readers.py:13`

**Inline comments:**
- `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:78`)
- `# children: subgrupos o detalle` (`encino_rpt/aggregation.py:324`)
- `# Contexto interno (no serializado)...` (`encino_rpt/models.py:123`)
- `# fase C sobre los hijos (grupos/detalle), antes de añadir chart/pivot` (`aggregation.py:349`)
- `# dividir cada fila una sola vez (PERF-02)` (`aggregation.py:260`)
- Regression tags in tests: `# CORR-08`, `# CORR-11`, `# TMPL-01`, `# TEST-01`, `# JSON-01`, `# MA-01`, `# P1`–`# P5`

## Function Design

**Size:** Prefer small single-purpose functions. Builders are broken into `add_field`, `set_format`, `add_style`, `link`, `image`, etc. The engine is decomposed into `_validate`, `_visible_columns`, `_enrich`, `_partition`, `_build_group_tree`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_render_templates`, `_build_kpis` (`encino_rpt/aggregation.py`).

**Parameters:**
- Keyword-only parameters after `*` for optional config: `def set_format(self, column: str, *, kind: str = "number", ...)` (`encino_rpt/report.py:119-131`), `def add_field(self, name: str, expression: str | None = None, *, after: str | None = None, ...)` (`report.py:222-232`)
- `**style`/`**opts` for open-ended config: `add_style(..., **style)` (`report.py:161`), `read(..., **opts)` (`encino_rpt/readers.py:351`)

**Return Values:**
- Fluent builder methods always return `self` (or `Section`) for chaining, with `Returns:` docstring noting "El propio reporte (fluido)."

## Module Design

**Exports:**
- `encino_rpt/__init__.py` re-exports 16 public names via `__all__` (`__init__.py:21-37`). `Section` is intentionally NOT exported (reachable only via `Report.group()`/`Report.section()`).
- `encino_rpt/renderers/__init__.py` exports the 7 renderer classes via `__all__` (`renderers/__init__.py:11-19`).

**Barrel files:**
- Only `encino_rpt/__init__.py` and `encino_rpt/renderers/__init__.py` act as barrels. Internal modules are imported directly by path (e.g. `from encino_rpt.expressions import evaluate`, `from encino_rpt.renderers._sanitize import is_dangerous`).

**Model/spec layout:**
- `encino_rpt/models.py` — pydantic `BaseModel` canonical tree (13 models), `Field(default_factory=...)` for mutable defaults, `PrivateAttr` for non-serialized context, recursive `Group.children` resolved with `Group.model_rebuild()` at module bottom (`models.py:368`)
- `encino_rpt/_specs.py` — internal `@dataclass` specs, `field(default_factory=list)` for mutable defaults
- `encino_rpt/aggregation.py` — the engine (enrich, group tree, totals, deferred resolution, templates, KPIs)
- `encino_rpt/readers.py` — multi-format readers with a `Reader` `Protocol`, a module-level `_READERS` registry, and built-in readers registered at import time (`readers.py:375-380`)
- `encino_rpt/renderers/` — visitor-style renderers consuming the shared `walk()` generator

## Patterns to Follow

- **Fluent builder**: validate immediately (raise early) and return `self`
- **"Truthiness coalescing" for label fallbacks**: `label = t.label or t.name or t.operator` (`encino_rpt/renderers/csv.py:55`, also `text.py:46`, `html.py:71`, `pdf.py:96`, `excel.py:107`, `markdown.py:126`)
- **Dict `or` fallback for user config**: `self.classes = classes or {}`, `self.styles = styles or {}`, `spec.options or {}`
- **Module-level `_OPS`-style dispatch dicts** instead of if/else chains for operator lookup: `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`encino_rpt/expressions.py:10-42`), `_OPS` (`renderers/html.py:12-19`), `_COLOR_OPS` (`renderers/excel.py:10-17`), `_FORMAT_BY_EXT` (`encino_rpt/readers.py:318-325`)
- **Preserve insertion order explicitly** where dicts don't: `_ordered_unique` (`encino_rpt/pivot.py:49-56`), `order` list parallel to `index` dict in `_partition` (`encino_rpt/aggregation.py:178-189`)
- **Pydantic recursive model** resolved with `Group.model_rebuild()` (`encino_rpt/models.py:368`)
- **JSON versioning**: `JsonRenderer.to_dict` injects `schema_version` via `{"schema_version": SCHEMA_VERSION, **result.model_dump(mode="json")}` (`encino_rpt/renderers/json.py:55`)
- **Streaming renderers**: each renderer exposes `render()` (full string), `iter_*()` (generator of lines/fragments), and `write()` (streams to a file-like) — e.g. `MarkdownRenderer.iter_markdown`/`write` (`encino_rpt/renderers/markdown.py:66-90`), mirrored by `ReportResult.iter_html`/`iter_csv`/`iter_text`/`iter_markdown` convenience methods (`encino_rpt/models.py:192-315`)

---

*Convention analysis: 2026-09-17*
