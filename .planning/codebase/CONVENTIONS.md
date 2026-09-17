# Coding Conventions

**Analysis Date:** 2026-09-17

> **⚠️ Important current-state note:** The canonical data model in `encino_rpt/models.py` now uses **stdlib `dataclasses`**, NOT pydantic. Serialization is handled by a dedicated `encino_rpt/_serialize.py` (stdlib only). The `[tool.mypy]` config has **no pydantic plugin**. Any older docs describing pydantic models are stale — do not write new pydantic models here.

## Naming Patterns

**Files (modules):**
- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`, `readers.py`
- Leading underscore for internal/private modules: `encino_rpt/_specs.py`, `encino_rpt/_serialize.py`, `encino_rpt/renderers/_format.py`, `encino_rpt/renderers/_sanitize.py`, `encino_rpt/renderers/_walk.py`
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_readers.py`, `test_perf_smoke.py`

**Classes (PascalCase):**
- Builder/facade: `Report`, `Section`, `Reader` (Protocol)
- Canonical model dataclasses: `Link`, `Image`, `Format`, `Total`, `Detail`, `Series`, `Chart`, `Pivot`, `ConditionalRule`, `Kpi`, `Group`, `ReportMeta`, `ReportResult`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `MarkdownRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)
- Internal reader classes: `_DelimitedReader` (underscore-prefixed), `JsonReader`, `JsonLinesReader`, `TuplesReader`, `ExcelReader` (`encino_rpt/readers.py`)
- Internal trie node `_PathNode` prefixed `_` (`encino_rpt/aggregation.py:270`)
- Test-local helper class `_MiReader` prefixed `_` (`tests/test_readers.py:128`)

**Functions/methods (`snake_case`):**
- Public API: `add_function`, `build_chart`, `build_pivot`, `format_value`, `sanitize_csv`, `evaluate`, `render`, `render_template` (imported as `render`), `build`, `walk`, `to_jsonable`, `from_dict`, `register_reader`, `read`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_build_group`, `_build_instance`, `_build_path_group`, `_apply_order`, `_compute_totals_into`, `_resolve_deferred`, `_render_templates`, `_build_kpis`, `_enrich`, `_esc`, `_wrap`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_assert_hashable`, `_make_path_node`, `_segs`, `_walk`, `_full_row`, `_total_row`, `_cell_attrs`, `_style_attr`, `_style_items`, `_css_decls`, `_style_block`, `_matched_rules`, `_add_thousands`, `_md_escape`, `_md_url`, `_md_cell`, `_md_table`, `_coerce` (both `readers._coerce` and `_serialize._coerce`), `_build` (`_serialize.py`), `_read_text`, `_read_text_auto`, `_resolve_format`, `_value_for`, `_aggregate`, `_as_format`, `_make_total`, `_make_value_fn`, `_label` (`charts.py`)
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the accepted cross-module abbreviations.

**Variables (`snake_case`):**
- `rows`, `visible_set`, `child_pairs`, `deferred`, `registry`, `children_map`, `root_spec`, `spec`, `sources`, `children`, `row_values`, `col_values`
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._aggregates`, `self._fields`, `self._detail`, `self._detail_source`, `self._groups`, `self._order`, `self._formats`, `self._styles`, `self._datasets`, `self._kpis` (`encino_rpt/report.py:29-42`), `self._spec` (`encino_rpt/section.py:12`), `self._delimiter` (`encino_rpt/readers.py:165`)
- Transient instance state (set during `render`, NOT in `__init__`): `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:51-54`), `self._normal` (`encino_rpt/renderers/pdf.py:51`)
- Post-init context replicated from the old pydantic `PrivateAttr` via `__post_init__`: `self._first_row`, `self._header_tpl`, `self._footer_tpl` (`encino_rpt/models.py:133-138`)

**Constants (`UPPER_SNAKE`, module-level):**
- `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:46-48`)
- `_TOKEN` regex (`encino_rpt/template.py:7`)
- `_DANGEROUS_PREFIXES`, `_LEADING_TRIM` (`encino_rpt/renderers/_sanitize.py:7-9`)
- `_SAFE_PROP`, `_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:22-23`)
- `SCHEMA_VERSION = "1.0"`, `_DEPTH_ERROR` (`encino_rpt/renderers/json.py:9-14`)
- `_READERS` registry (`encino_rpt/readers.py:35`), `_FORMAT_BY_EXT` map (`encino_rpt/readers.py:318-325`)
- Operator dispatch tables: `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`encino_rpt/expressions.py:10-43`), `_OPS` (`encino_rpt/renderers/html.py:13-20`), `_COLOR_OPS` (`encino_rpt/renderers/excel.py:10-17`)
- `_NODES` discriminator map, `_UNION` (`encino_rpt/_serialize.py:14-22`)
- Type alias `Child = Detail | Group | Chart | Pivot` (`encino_rpt/aggregation.py:28`)

## Code Style

**Formatting:**
- Tool: `ruff` `0.16.7` (dev dependency, `pyproject.toml:50`)
- `[tool.ruff]` (`pyproject.toml:69-72`): `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`
- `[tool.ruff.format]` (`pyproject.toml:74-75`): `quote-style = "double"`
- Line length 88 (enforced by `ruff format --check encino_rpt tests` in CI, `.github/workflows/ci.yml:50`)
- Indentation: 4 spaces throughout
- Double quotes for all string literals

**Linting:**
- Tool: `ruff` `0.16.7`, run with defaults `uv run ruff check` (`.github/workflows/ci.yml:30`). No `select`/`ignore` pinned — ruff defaults only.

**Type checking:**
- Tool: `mypy` `2.3.1` (dev dependency, `pyproject.toml:51`). Config `[tool.mypy]` (`pyproject.toml:60-67`):
  - `python_version = "3.10"`
  - `check_untyped_defs = true`
  - `warn_unused_ignores = true`
  - `warn_redundant_casts = true`
  - `no_implicit_optional = true`
  - `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs)
  - **No pydantic plugin** (the old `plugins = ["pydantic.mypy"]` line is gone — the model layer is now stdlib dataclasses)
- Run with `uv run mypy encino_rpt` (`.github/workflows/ci.yml:47`)

**Typing idioms:**
- `from __future__ import annotations` at the top of **every** module (enables PEP 604 unions and builtin generics)
- Prefer `str | None` over `Optional[str]`; builtin generics (`list[dict]`, `dict[str, Any]`) everywhere
- `Any` for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`
- Optional config params sometimes untyped where the type is obvious from context: `def add_function(self, name: str, fn)` (`encino_rpt/report.py:93`), `format=None` (`encino_rpt/report.py:213`)

## Data Model & Serialization (current)

- Every node in `encino_rpt/models.py` is a `@dataclass` with a discriminating `type: Literal[...]` field defaulting to its own literal (`"group"`, `"detail"`, `"chart"`, `"pivot"`, `"kpi"`, `"link"`, `"image"`). This is what `_serialize._NODES` dispatches on.
- Mutable defaults always use `field(default_factory=...)` — e.g. `children: list[...] = field(default_factory=list)` (`encino_rpt/models.py:131`), `params: list[Any] = field(default_factory=list)` (`models.py:146`).
- `Group.__post_init__` sets non-field context attrs (`_first_row`, `_header_tpl`, `_footer_tpl`) that are excluded from serialization by the `startswith("_")` filter in `_serialize.to_jsonable` (`encino_rpt/_serialize.py:42`).
- Round-trip serialization lives in `encino_rpt/_serialize.py`: `to_jsonable(obj)` converts dataclasses → native JSON types (handling `Decimal`, `datetime`/`date`/`time`, `Enum`); `from_dict(data)` reconstructs via `get_type_hints` + `_coerce`. No pydantic anywhere.
- `schema_version` is injected **only** by `JsonRenderer` (`{"schema_version": SCHEMA_VERSION, **data}` in `encino_rpt/renderers/json.py:52`). `ReportResult.to_dict()` returns the bare tree with no version field (`encino_rpt/models.py:165-174`).

## Import Organization

**Order (blank-line separated groups):**
1. `from __future__ import annotations`
2. stdlib (alphabetical) — e.g. `import ast`, `import operator` (`encino_rpt/expressions.py:5-8`); `import csv`, `io`, `json`, `math`, `pathlib`, `typing` (`encino_rpt/readers.py:5-10`)
3. relative/package imports (alphabetical) — e.g. `from ._specs import ...`, `from .charts import build_chart`, `from .models import ...` (`encino_rpt/aggregation.py:8-25`)

**Relative import form:**
- `from ._specs import FieldSpec` (`encino_rpt/report.py:7`)
- `from ..models import Image, Link` (`encino_rpt/renderers/csv.py:9`)
- `from .._serialize import to_jsonable` (`encino_rpt/renderers/json.py:7`)
- No path aliases configured (only `pythonpath = ["."]` in `pyproject.toml:43`). No `import`-rewriting.

**Lazy imports (to break cycles / isolate optional deps):**
- `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:432`)
- `from .readers import read as read_rows` inside `Report.read()` (`encino_rpt/report.py:75`); `from .readers import register_reader` inside `Report.register_reader()` (`report.py:88`)
- `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html`/`iter_html` (`encino_rpt/models.py:232,267`); same pattern for csv/text/excel/json/pdf/markdown (`models.py:289,320,353,381,399,415`)
- `from ._serialize import ...` inside `ReportResult.to_dict`/`from_dict` (`models.py:172,186`)
- `from openpyxl import load_workbook` inside `ExcelReader.read` (`encino_rpt/readers.py:296`)
- `from openpyxl import Workbook` + `from openpyxl.styles import Font` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:41-42`); further per-helper imports: `from openpyxl.utils import get_column_letter` in `_sum_formula` (`excel.py:145`), `from openpyxl.chart import ...` in `_chart` (`excel.py:212`)
- `from reportlab.platypus import ...` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:36-44`); `from reportlab.platypus import Paragraph` inside `_cell`/`_full`/`_pivot_table` (`pdf.py:131,143,149`)

## Error Handling

**Custom exceptions (both subclass `ValueError`):**
- `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:51`)
- `class AggregationError(ValueError)` (`encino_rpt/aggregation.py:31`)

**Exception choice by situation:**
- `ValueError` for invalid config: `"`columns` y `path` son excluyentes"` (`encino_rpt/report.py:389`), `"corte ya declarado: {name!r}"` (`report.py:391`), `"kind inválido: {kind!r}"` (`report.py:149`), `"dirección de orden inválida: {direction!r}"` (`encino_rpt/section.py:164`), `"`columns` requerido para reader 'tuples'"` (`encino_rpt/readers.py:265`)
- `KeyError` for unknown named lookups: `"corte no declarado: {name!r}"` (`encino_rpt/report.py:423`)
- `IndexError` for out-of-range param access: `"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:27`)
- `TypeError` for unsupported sources: `"fuente no soportada: {type(source).__name__!r}"` (`encino_rpt/readers.py:127`), and for non-list/non-dict JSON payloads (`readers.py:207,211,242`)
- `ImportError` for missing optional deps, always re-raised with `from exc` and a Spanish install hint: `"openpyxl no está instalado; instala el extra `excel`"` (`encino_rpt/renderers/excel.py:44-46`, `encino_rpt/readers.py:298-300`), `"reportlab no está instalado; instala el extra `pdf`"` (`encino_rpt/renderers/pdf.py:45-48`). Both branches carry `# pragma: no cover - depende del entorno`.

**Context wrapping:**
- `_wrap(context, fn, *args)` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:35-44`). Used for field enrichment (`campo {name!r} (fila {index})`), totals (`total {name or operator!r} (grupo {spec.name!r})`), deferred totals, KPIs (`kpi {spec.label!r}`), charts (`gráfico (grupo ...)`), pivots (`pivote (grupo ...)`).
- Error messages include the failing name/value via `{x!r}` for clarity: `"valor no hashable en la columna de agrupación {c!r}: {value!r}"` (`aggregation.py:205`).

**Controlled recursion translation:**
- `JsonRenderer.render`/`to_dict` catch `RecursionError` and re-raise `ValueError` with a clear `"la jerarquía es demasiado profunda..."` message (`encino_rpt/renderers/json.py:34-51`). Non-serializable values must still raise `TypeError` (not be masked as "deep") — see `test_to_json_non_serializable_not_masked`.

**Do not swallow:** the engine never catches exceptions; a failing expression propagates up through `run()` to the caller.

## Logging

- **No logging framework.** No `logging` imports anywhere in `encino_rpt/`. Errors surface as exceptions; no runtime logging, no `print`. The library is pure and side-effect-free.

## Comments

**Module docstrings:**
- One-line Spanish docstring in every module: `"""Builder fluido `Report`."""` (`encino_rpt/report.py:1`), `"""Evaluador seguro de expresiones (sin `eval`, whitelist vía `ast`)."""` (`encino_rpt/expressions.py:1`), `"""Modelo de datos canónico del reporte (dataclasses stdlib, serializable a JSON)."""` (`encino_rpt/models.py:1`)

**Docstrings on public API:**
- Google-style (Spanish) with `Args:`, `Returns:`, `Raises:`, and `Yields:` sections — see `Report.group` (`encino_rpt/report.py:360-386`), `ReportResult.to_excel` (`encino_rpt/models.py:371-383`), `ReportResult.iter_html` (`encino_rpt/models.py:246-265`), `readers.read` (`encino_rpt/readers.py:350-371`)

**Section banner comments:**
- `# --- funciones / campos ---` (`encino_rpt/report.py:92`), `# --- detalle / grupos ---` (`report.py:343`), `# --- enriquecimiento ---` (`encino_rpt/aggregation.py:121`), `# --- árbol de grupos ---` (`aggregation.py:166`), `# --- fase B ---` (`aggregation.py:493`), `# --- plantillas (fase final) ---` (`aggregation.py:510`)
- In tests: `# --- P1: inyección de fórmulas ---` and similar (`tests/test_security.py`), `# --- auto-detección de tipos (_coerce) ---` (`tests/test_readers.py:13`)

**Inline rationale comments:**
- `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:78`)
- `# dividir cada fila una sola vez (PERF-02)` (`encino_rpt/aggregation.py:284`)
- `# fase C sobre los hijos (grupos/detalle), antes de añadir chart/pivot` (`aggregation.py:373`)
- `# Contexto interno (no serializado)...` (`encino_rpt/models.py:133`)
- `# pragma: no cover - depende del entorno` on optional-dep import guards

**Regression tags:** tests reference issue IDs in comments: `# CORR-08`, `# CORR-09`, `# CORR-11`, `# CORR-12`, `# CORR-13`, `# CORR-14`, `# TMPL-01`, `# TMPL-02`, `# TMPL-03`, `# TEST-01`, `# JSON-01`, `# FEAT-02`, `# D-02`, `# PERF-02`, `# P1`–`# P5`, `# MA-01`.

## Function Design

**Keyword-only params:** optional config follows `*`:
- `def set_format(self, column: str, *, kind: str = "number", ...)` (`encino_rpt/report.py:119-130`)
- `def add_field(self, name: str, expression: str | None = None, *, after: str | None = None, ...)` (`report.py:235-244`)
- `def order_by(self, column=None, *, direction="asc", total=None, expression=None)` (`encino_rpt/section.py:144-150`)

**Open-ended kwargs:**
- `**style` for styles (`encino_rpt/report.py:166-172`), `**opts` for readers (`encino_rpt/readers.py:351`) and PDF (`encino_rpt/renderers/pdf.py:17-19`)

**Fluent builder:** all `Report`/`Section` mutators return `self` (or `Section`) for chaining, with a `Returns:` docstring noting "El propio reporte (fluido)." Validation raises immediately (early), then returns `self`.

## Module Design

**Barrels (only two):**
- `encino_rpt/__init__.py` re-exports the 15 public names via `__all__` (`__init__.py:21-37`): `Chart`, `ConditionalRule`, `Detail`, `Format`, `Group`, `Image`, `Kpi`, `Link`, `Pivot`, `Reader`, `Report`, `ReportMeta`, `ReportResult`, `Series`, `Total`. `Section` is intentionally NOT exported (reachable only via `Report.group()`/`Report.section()`).
- `encino_rpt/renderers/__init__.py` exports the 7 renderer classes via `__all__` (`renderers/__init__.py:11-19`).
- Everything else is imported by direct module path: `from encino_rpt.expressions import evaluate`, `from encino_rpt.renderers._sanitize import is_dangerous`.

**Module responsibilities:**
- `encino_rpt/models.py` — stdlib `@dataclass` canonical tree (13 models), `type: Literal[...]` discriminators, `field(default_factory=...)` for mutable defaults, `__post_init__` for non-serialized context
- `encino_rpt/_specs.py` — internal `@dataclass` builder specs, `field(default_factory=list)` for mutable defaults
- `encino_rpt/_serialize.py` — stdlib JSON round-trip (no pydantic): `to_jsonable`, `_build`, `_coerce`, `from_dict`
- `encino_rpt/aggregation.py` — the engine (enrich, group tree, totals, deferred resolution, templates, KPIs)
- `encino_rpt/readers.py` — multi-format readers with a `Reader` `Protocol`, a module-level `_READERS` registry, and built-in readers registered at import time (`readers.py:375-380`)
- `encino_rpt/renderers/` — visitor-style renderers consuming the shared `walk()` generator

## Patterns to Follow

- **Fluent builder**: validate immediately (raise early) and return `self`
- **"Truthiness coalescing" for label fallbacks**: `label = t.label or t.name or t.operator` (`encino_rpt/renderers/csv.py:83`, also `text.py:69`, `html.py:117`, `pdf.py:102`, `excel.py:103`, `markdown.py:126`)
- **Dict `or` fallback for user config**: `self.classes = classes or {}` (`encino_rpt/renderers/html.py:38`), `spec.options or {}` (`encino_rpt/pivot.py:49`, `charts.py:31`)
- **Module-level `_OPS`-style dispatch dicts** instead of if/else chains for operator lookup: `_BINOPS`/`_UNARY`/`_CMP`/`_FUNCTIONS` (`encino_rpt/expressions.py:10-43`), `_OPS` (`renderers/html.py:13-20`), `_COLOR_OPS` (`renderers/excel.py:10-17`), `_FORMAT_BY_EXT` (`encino_rpt/readers.py:318-325`)
- **Preserve insertion order explicitly** where dicts don't: `_ordered_unique` (`encino_rpt/pivot.py:53-60`), `order` list parallel to `index` dict in `_partition` (`encino_rpt/aggregation.py:189-212`)
- **Discriminator-driven reconstruction**: `_NODES` maps `type` literal → node class (`encino_rpt/_serialize.py:17-22`)
- **JSON versioning**: `JsonRenderer.to_dict` injects `schema_version` via `{"schema_version": SCHEMA_VERSION, **data}` (`encino_rpt/renderers/json.py:52`)
- **Streaming renderers**: each renderer exposes `render()` (full string/bytes), `iter_*()` (generator), and `write()` (streams to a file-like) — e.g. `MarkdownRenderer.iter_markdown`/`write` (`encino_rpt/renderers/markdown.py:66-90`), mirrored by `ReportResult.iter_html`/`iter_csv`/`iter_text`/`iter_markdown` (`encino_rpt/models.py:246-369`)
- **Lazy imports** for optional deps and cycle-breaking (see Import Organization)

---

*Convention analysis: 2026-09-17*
