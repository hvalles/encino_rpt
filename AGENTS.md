<!-- GSD:project-start source:PROJECT.md -->

## Project

**encino-rpt**

`encino-rpt` es un reporteador financiero en Python que consume `list[dict]` (la salida de consultas ya materializadas) y produce un **árbol canónico de datos** (pydantic, serializable a JSON) con renderers opcionales a HTML, Excel, CSV, PDF y texto. Está dirigido a desarrolladores que necesitan reportes financieros — jerarquías de cortes, totales, pivotes, gráficos, KPIs y celdas enriquecidas (enlaces/imágenes) — sin acoplarse a un motor de base de datos.

**Core Value:** Producir reportes financieros **correctos y seguros**: la agregación y el renderizado deben dar resultados exactos, idempotentes y sin inyecciones, siempre.

### Constraints

- **Tech stack**: Python `>=3.10`; `pydantic>=2` como única dependencia de runtime; `openpyxl` (extra `excel`) y `reportlab` (extra `pdf`) opcionales.
- **Seguridad**: nunca `eval`; evaluador de expresiones con whitelist `ast`; sanitización de fórmulas (OWASP) en Excel/CSV.
- **Compatibilidad**: no romper la API pública existente (`Report`, `Section`, `ReportResult`, `to_*`/`render_*`).
- **Rendimiento**: diseño in-memory; agregados pesados se delegan a SQL (no-objetivo documentado).

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python `>=3.10` — the entire library is pure Python (stdlib only). Declared via `requires-python = ">=3.10"` in `pyproject.toml:13`. Classifiers declare support for 3.10–3.13 (`pyproject.toml:24-28`). No compiled extensions, no C/Rust wheels.
- None detected. No TypeScript/JS, no templated source files. HTML/Markdown/CSV/JSON/text/PDF output is generated programmatically inside `encino_rpt/renderers/`. Markdown is used only for docs (`docs/*.md`).

## Runtime

- CPython only. This is a **library**, not an application/server — no server runtime, no web framework, no worker process, no async loop. Local dev venv at `.venv/` (gitignored via `.gitignore`). CI runs on `ubuntu-latest`.
- `uv` (Astral). Lockfile `uv.lock` (lockfile version 1, ~300 KB) at repo root. All dependency versions are pinned there. No `requirements.txt` — `pyproject.toml`-only.
- Lockfile: present (`uv.lock`).

## Frameworks

- **None — zero runtime dependencies.** The package ships no mandatory third-party runtime deps. `[project]` has no `dependencies` key at all (`pyproject.toml:8-31`).
- The canonical data model (`ReportResult`, `Group`, `Detail`, `Total`, `Chart`, `Pivot`, `Kpi`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`) is implemented as stdlib `@dataclass` classes in `encino_rpt/models.py` (pydantic removed entirely). Mutable defaults use `field(default_factory=...)`.
- JSON serialization is a custom stdlib module `encino_rpt/_serialize.py` (`to_jsonable`, `_build`, `_coerce`, `from_dict`) replacing `model_dump(mode="json")` / `model_validate`. It converts `Decimal`→`str`, `datetime/date/time`→`isoformat()`, `Enum`→`.value`, and dispatches the recursive `Group.children` union on the `type` discriminator via `_NODES` (`_serialize.py:17-22`).
- **pytest** `9.1.1` — dev group (`pyproject.toml:47`). Config `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `pythonpath = ["."]` (`pyproject.toml:41-43`).
- **pytest-cov** `7.1.0` — dev group (`pyproject.toml:52`). Backed by **coverage** `7.16.1` (transitive). Config in `[tool.coverage.run]`/`[tool.coverage.report]` (`pyproject.toml:77-84`) and enforced in CI via `--cov-fail-under=80` (`.github/workflows/ci.yml:53`). Current measured coverage: **91%** (129 tests).
- **hatchling** — build backend declared in `[build-system]` (`pyproject.toml:1-3`). Wheel packages `["encino_rpt"]` (`pyproject.toml:6`).
- **mypy** `2.3.1` — dev group (`pyproject.toml:51`). Config `[tool.mypy]` (`pyproject.toml:60-67`): `python_version = "3.10"`, `check_untyped_defs`, `warn_unused_ignores`, `warn_redundant_casts`, `no_implicit_optional`, and `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs). **No `pydantic.mypy` plugin.**
- **ruff** `0.16.7` — linter + formatter, dev group (`pyproject.toml:50`). `[tool.ruff]` (`pyproject.toml:69-72`): `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`; `[tool.ruff.format]` (`pyproject.toml:74-75`): `quote-style = "double"`.
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs group, `pyproject.toml:54-58`), configured in `mkdocs.yml`.

## Key Dependencies

- **None.** The library has zero mandatory runtime dependencies. It runs on Python stdlib alone (`dataclasses`, `typing`, `json`, `csv`, `io`, `math`, `pathlib`, `ast`, `decimal`, `datetime`, `enum`, `operator`, `re`, `html`, `collections.abc`, `types`). Verified via full import scan: no `urllib`, `requests`, `socket`, `http`, or any third-party import at module level in `encino_rpt/`.
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml:34`, `openpyxl>=3.1.5`). Imported lazily inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:40-46`) and `ExcelReader.read` (`encino_rpt/readers.py:296-299`). Raises `ImportError` with a Spanish hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml:35`, `reportlab>=5.0.1`). Imported lazily inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:35-48`). Same guarded-import pattern. Pulls **pillow** `12.3.0` (transitive).
- dev group (`pyproject.toml:45-53`): pytest, openpyxl, reportlab, ruff, mypy, pytest-cov
- docs group (`pyproject.toml:54-58`): mkdocs, mkdocs-material, mkdocstrings[python]

## Configuration

- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required. `.env` is listed in `.gitignore` but no such file exists.
- `pyproject.toml` — hatchling build config, project metadata (name `encino-rpt`, version `0.3.0`), optional-dependency extras (`excel`, `pdf`), dependency groups (dev/docs), and tool configs for pytest/mypy/ruff/coverage.
- `mkdocs.yml` — docs config (material theme, `language: es`, mkdocstrings handler with `docstring_style: google`, 5-page nav).
- `.github/workflows/ci.yml` — CI with two jobs: `test` (matrix 3.10–3.13, runs `pytest` + `ruff check`) and `quality` (singleton 3.13, runs `mypy encino_rpt` + `ruff format --check` + coverage `--cov-fail-under=80`).
- `.github/workflows/docs.yml` — builds docs with `uv sync --group docs` + `mkdocs build`, deploys to GitHub Pages.
- `.github/workflows/publish.yml` — `uv build`, publishes to TestPyPI (main) and PyPI (tags `v*`).

## Platform Requirements

- Python 3.10+ installed via `uv python install` (`.github/workflows/ci.yml:21`).
- `uv sync --all-extras --group dev` installs the full dev environment (`.github/workflows/ci.yml:24`).
- `uv run pytest` runs the suite (129 tests); `uv run ruff check` lints; `uv run ruff format --check encino_rpt tests` checks formatting; `uv run mypy encino_rpt` type-checks; `uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80` enforces ≥80% coverage (currently 91%).
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml`. Docs hosted on GitHub Pages (`https://hvalles.github.io/encino_rpt/`). No application hosting — this is a library. Version `0.3.0` in `pyproject.toml:10`.
- Windows local dev (this repo lives on `win32`) but CI runs Linux; no OS-specific code detected in `encino_rpt/` (pure stdlib + optional openpyxl/reportlab).

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`, `readers.py`
- Leading underscore for internal/private modules: `encino_rpt/_specs.py`, `encino_rpt/_serialize.py`, `encino_rpt/renderers/_format.py`, `encino_rpt/renderers/_sanitize.py`, `encino_rpt/renderers/_walk.py`
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_readers.py`, `test_perf_smoke.py`
- Builder/facade: `Report` (`encino_rpt/report.py`), `Section` (`encino_rpt/section.py`), `Reader` (Protocol, `encino_rpt/readers.py`)
- Canonical model dataclasses: `Link`, `Image`, `Format`, `Total`, `Detail`, `Series`, `Chart`, `Pivot`, `ConditionalRule`, `Kpi`, `Group`, `ReportMeta`, `ReportResult` (`encino_rpt/models.py`)
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `MarkdownRenderer`, `PdfRenderer`, `TextRenderer` (`encino_rpt/renderers/`)
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (`encino_rpt/_specs.py`)
- Internal reader classes: `_DelimitedReader` (underscore-prefixed), `JsonReader`, `JsonLinesReader`, `TuplesReader`, `ExcelReader` (`encino_rpt/readers.py`)
- Internal trie node `_PathNode` prefixed `_` (`encino_rpt/aggregation.py:270`)
- Test-local helper class `_MiReader` prefixed `_` (`tests/test_readers.py:128`)
- Public API: `add_function`, `build_chart`, `build_pivot`, `format_value`, `excel_number_format`, `sanitize_csv`, `is_dangerous`, `evaluate`, `render`, `render_template` (imported as `render`), `build`, `walk`, `to_jsonable`, `from_dict`, `register_reader`, `read`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_build_group`, `_build_instance`, `_build_path_group`, `_apply_order`, `_compute_totals_into`, `_resolve_deferred`, `_render_templates`, `_build_kpis`, `_enrich`, `_esc`, `_wrap`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_assert_hashable`, `_make_path_node`, `_segs`, `_walk`, `_full_row`, `_total_row`, `_cell_attrs`, `_style_attr`, `_style_items`, `_css_decls`, `_style_block`, `_matched_rules`, `_add_thousands`, `_md_escape`, `_md_url`, `_md_cell`, `_md_table`, `_coerce` (both `readers._coerce` and `_serialize._coerce`), `_build` (`_serialize.py`), `_read_text`, `_read_text_auto`, `_resolve_format`, `_value_for`, `_aggregate`, `_as_format`, `_make_total`, `_make_value_fn`, `_label` (`charts.py`)
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the accepted cross-module abbreviations.
- `rows`, `visible_set`, `child_pairs`, `deferred`, `registry`, `children_map`, `root_spec`, `spec`, `sources`, `children`, `row_values`, `col_values`
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._aggregates`, `self._fields`, `self._detail`, `self._detail_source`, `self._groups`, `self._order`, `self._formats`, `self._styles`, `self._datasets`, `self._kpis` (`encino_rpt/report.py:29-42`), `self._spec` (`encino_rpt/section.py:12`), `self._delimiter` (`encino_rpt/readers.py:165`)
- Transient instance state (set during `render`, NOT in `__init__`): `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:51-54`), `self._normal` (`encino_rpt/renderers/pdf.py:51`)
- Post-init context replicated from the old pydantic `PrivateAttr` via `__post_init__`: `self._first_row`, `self._header_tpl`, `self._footer_tpl` (`encino_rpt/models.py:133-138`)
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

- Tool: `ruff` `0.16.7` (dev dependency, `pyproject.toml:50`)
- `[tool.ruff]` (`pyproject.toml:69-72`): `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`
- `[tool.ruff.format]` (`pyproject.toml:74-75`): `quote-style = "double"`
- Line length 88 (enforced by `ruff format --check encino_rpt tests` in CI, `.github/workflows/ci.yml:50`)
- Indentation: 4 spaces throughout
- Double quotes for all string literals
- Tool: `ruff` `0.16.7`, run with defaults `uv run ruff check` (`.github/workflows/ci.yml:30`). No `select`/`ignore` pinned — ruff defaults only.
- Tool: `mypy` `2.3.1` (dev dependency, `pyproject.toml:51`). Config `[tool.mypy]` (`pyproject.toml:60-67`): `python_version = "3.10"`, `check_untyped_defs = true`, `warn_unused_ignores = true`, `warn_redundant_casts = true`, `no_implicit_optional = true`, `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs). **No pydantic plugin.**
- Run with `uv run mypy encino_rpt` (`.github/workflows/ci.yml:47`)
- `from __future__ import annotations` at the top of **every** module (enables PEP 604 unions and builtin generics)
- Prefer `str | None` over `Optional[str]`; builtin generics (`list[dict]`, `dict[str, Any]`) everywhere
- `Any` for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`
- Optional config params sometimes untyped where the type is obvious from context: `def add_function(self, name: str, fn)` (`encino_rpt/report.py:93`), `format=None` (`encino_rpt/report.py:213`)

## Data Model & Serialization

- Every node in `encino_rpt/models.py` is a `@dataclass` with a discriminating `type: Literal[...]` field defaulting to its own literal (`"group"`, `"detail"`, `"chart"`, `"pivot"`, `"kpi"`, `"link"`, `"image"`). This is what `_serialize._NODES` dispatches on.
- Mutable defaults always use `field(default_factory=...)` — e.g. `children: list[...] = field(default_factory=list)` (`encino_rpt/models.py:131`), `params: list[Any] = field(default_factory=list)` (`models.py:146`).
- `Group.__post_init__` sets non-field context attrs (`_first_row`, `_header_tpl`, `_footer_tpl`) that are excluded from serialization by the `startswith("_")` filter in `_serialize.to_jsonable` (`encino_rpt/_serialize.py:42`).
- Round-trip serialization lives in `encino_rpt/_serialize.py`: `to_jsonable(obj)` converts dataclasses → native JSON types (handling `Decimal`, `datetime`/`date`/`time`, `Enum`); `from_dict(data)` reconstructs via `get_type_hints` + `_coerce`. No pydantic anywhere.
- `schema_version` is injected **only** by `JsonRenderer` (`{"schema_version": SCHEMA_VERSION, **data}` in `encino_rpt/renderers/json.py:52`). `ReportResult.to_dict()` returns the bare tree with no version field (`encino_rpt/models.py:165-174`).

## Import Organization

- No path aliases configured. Only `pythonpath = ["."]` in `pyproject.toml:43`. No `import`-rewriting.
- `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:432`)
- `from .readers import read as read_rows` inside `Report.read()` (`encino_rpt/report.py:75`); `from .readers import register_reader` inside `Report.register_reader()` (`report.py:88`)
- `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html`/`iter_html` (`encino_rpt/models.py:232,267`); same pattern for csv/text/excel/json/pdf/markdown (`models.py:289,320,353,381,399,415`)
- `from ._serialize import ...` inside `ReportResult.to_dict`/`from_dict` (`models.py:172,186`)
- `from openpyxl import load_workbook` inside `ExcelReader.read` (`encino_rpt/readers.py:296`)
- `from openpyxl import Workbook` + `from openpyxl.styles import Font` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:41-42`); further per-helper imports: `from openpyxl.utils import get_column_letter` in `_sum_formula` (`excel.py:145`), `from openpyxl.chart import ...` in `_chart` (`excel.py:212`)
- `from reportlab.platypus import ...` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:36-44`); `from reportlab.platypus import Paragraph` inside `_cell`/`_full`/`_pivot_table` (`pdf.py:131,143,149`)

## Error Handling

- `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:51`)
- `class AggregationError(ValueError)` (`encino_rpt/aggregation.py:31`)
- `ValueError` for invalid config: `"`columns` y `path` son excluyentes"` (`encino_rpt/report.py:389`), `"corte ya declarado: {name!r}"` (`report.py:391`), `"kind inválido: {kind!r}"` (`report.py:149`), `"dirección de orden inválida: {direction!r}"` (`encino_rpt/section.py:164`), `"`columns` requerido para reader 'tuples'"` (`encino_rpt/readers.py:265`)
- `KeyError` for unknown named lookups: `"corte no declarado: {name!r}"` (`encino_rpt/report.py:423`)
- `IndexError` for out-of-range param access: `"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:27`)
- `TypeError` for unsupported sources: `"fuente no soportada: {type(source).__name__!r}"` (`encino_rpt/readers.py:127`), and for non-list/non-dict JSON payloads (`readers.py:207,211,242`)
- `ImportError` for missing optional deps, always re-raised with `from exc` and a Spanish install hint: `"openpyxl no está instalado; instala el extra `excel`"` (`encino_rpt/renderers/excel.py:44-46`, `encino_rpt/readers.py:298-300`), `"reportlab no está instalado; instala el extra `pdf`"` (`encino_rpt/renderers/pdf.py:45-48`). Both branches carry `# pragma: no cover - depende del entorno`.
- `_wrap(context, fn, *args)` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:35-44`). Used for field enrichment (`campo {name!r} (fila {index})`), totals (`total {name or operator!r} (grupo {spec.name!r})`), deferred totals, KPIs (`kpi {spec.label!r}`), charts (`gráfico (grupo ...)`), pivots (`pivote (grupo ...)`).
- Error messages include the failing name/value via `{x!r}` for clarity: `"valor no hashable en la columna de agrupación {c!r}: {value!r}"` (`aggregation.py:205`).
- `JsonRenderer.render`/`to_dict` catch `RecursionError` and re-raise `ValueError` with a clear `"la jerarquía es demasiado profunda..."` message (`encino_rpt/renderers/json.py:34-51`). Non-serializable values must still raise `TypeError` (not be masked as "deep").

## Logging

- **No logging framework.** No `logging` imports anywhere in `encino_rpt/`. Errors surface as exceptions; no runtime logging, no `print`. The library is pure and side-effect-free.

## Comments

- One-line Spanish docstring in every module: `"""Builder fluido `Report`."""` (`encino_rpt/report.py:1`), `"""Evaluador seguro de expresiones (sin `eval`, whitelist vía `ast`)."""` (`encino_rpt/expressions.py:1`), `"""Modelo de datos canónico del reporte (dataclasses stdlib, serializable a JSON)."""` (`encino_rpt/models.py:1`)
- Section banner comments using `# --- area ---` to group related code: `# --- funciones / campos ---` (`encino_rpt/report.py:92`), `# --- detalle / grupos ---` (`report.py:343`), `# --- enriquecimiento ---` (`encino_rpt/aggregation.py:121`), `# --- árbol de grupos ---` (`aggregation.py:166`), `# --- fase B ---` (`aggregation.py:493`), `# --- plantillas (fase final) ---` (`aggregation.py:510`)
- Inline rationale comments explaining non-obvious behavior: `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:78`), `# dividir cada fila una sola vez (PERF-02)` (`encino_rpt/aggregation.py:284`), `# fase C sobre los hijos (grupos/detalle), antes de añadir chart/pivot` (`aggregation.py:373`), `# Contexto interno (no serializado)...` (`encino_rpt/models.py:133`)
- `# pragma: no cover - depende del entorno` on optional-dep import guards
- Google-style (Spanish) with `Args:`, `Returns:`, `Raises:`, and `Yields:` sections — see `Report.group` (`encino_rpt/report.py:360-386`), `ReportResult.to_excel` (`encino_rpt/models.py:371-383`), `ReportResult.iter_html` (`encino_rpt/models.py:246-265`), `readers.read` (`encino_rpt/readers.py:350-371`)

## Function Design

- Keyword-only arguments via `*` for optional config: `def set_format(self, column: str, *, kind: str = "number", ...)` (`encino_rpt/report.py:119-130`), `def add_field(self, name: str, expression: str | None = None, *, after: str | None = None, ...)` (`report.py:235-244`), `def order_by(self, column=None, *, direction="asc", total=None, expression=None)` (`encino_rpt/section.py:144-150`)
- `**kwargs` for open-ended style/option bags: `**style` for styles (`encino_rpt/report.py:166-172`), `**opts` for readers (`encino_rpt/readers.py:351`) and PDF (`encino_rpt/renderers/pdf.py:17-19`)

## Module Design

- `encino_rpt/__init__.py` re-exports the 15 public names via `__all__` (`__init__.py:21-37`): `Chart`, `ConditionalRule`, `Detail`, `Format`, `Group`, `Image`, `Kpi`, `Link`, `Pivot`, `Reader`, `Report`, `ReportMeta`, `ReportResult`, `Series`, `Total`. `Section` is intentionally NOT exported (reachable only via `Report.group()`/`Report.section()`).
- `encino_rpt/renderers/__init__.py` exports the 7 renderer classes via `__all__` (`renderers/__init__.py:11-19`).
- Everything else is imported by direct module path: `from encino_rpt.expressions import evaluate`, `from encino_rpt.renderers._sanitize import is_dangerous`.
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

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs, custom functions/aggregates; `read()`/`register_reader()` classmethods for multi-format input; `run()` materializes the tree | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a cut's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress_zero/page_break) | `encino_rpt/section.py` |
| `FieldSpec`/`GroupSpec`/`TotalSpec`/`ChartSpec`/`PivotSpec`/`KpiSpec` | Internal builder specifications (dataclasses) — NOT part of the canonical tree | `encino_rpt/_specs.py` |
| `Reader` (protocol) + registry | Multi-format input readers (csv/tsv/json/jsonl/tuples/excel + custom); `read()`/`register_reader()`/`get_reader()` | `encino_rpt/readers.py` |
| `evaluate()` | Safe expression evaluator (AST whitelist, no `eval`, anti-DoS limits) | `encino_rpt/expressions.py` |
| `render()` | `{{token}}` template interpolation for header/footer and link/image URLs | `encino_rpt/template.py` |
| `build()` | Orchestrates `run()`: validate, visible columns, row enrichment, group tree, totals, deferred `TOTAL(...)` resolution, template rendering, KPIs → `ReportResult` | `encino_rpt/aggregation.py` |
| `build_chart()` | Derives `Chart.labels`/`series` from already-aggregated child groups or the group's own totals | `encino_rpt/charts.py` |
| `build_pivot()` | Builds a rows × columns cross-tab matrix (`Pivot`) with row/column totals | `encino_rpt/pivot.py` |
| Canonical models | Serializable tree as **stdlib dataclasses**: `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta` | `encino_rpt/models.py` |
| `to_jsonable()`/`from_dict()` | JSON-native (de)serialization of the dataclass tree without pydantic | `encino_rpt/_serialize.py` |
| `walk()` | Shared iterative tree traversal; yields typed `(event, node)` tuples consumed by every renderer | `encino_rpt/renderers/_walk.py` |
| `HtmlRenderer` | Consumes `walk()` → HTML `<table>` with classes, conditional styles, pivot sub-tables, full-document `template` mode | `encino_rpt/renderers/html.py` |
| `ExcelRenderer` | Consumes `walk()` → openpyxl `Worksheet` (optional dep), native charts, `=SUM(...)` formula mode, cell formatting | `encino_rpt/renderers/excel.py` |
| `CsvRenderer` | Consumes `walk()` → flattened CSV with formula-injection sanitization | `encino_rpt/renderers/csv.py` |
| `TextRenderer` | Consumes `walk()` → indented plain text for inspection | `encino_rpt/renderers/text.py` |
| `MarkdownRenderer` | Consumes `walk()` → GFM tables, groups as headers; charts/pivots degrade to text/GFM | `encino_rpt/renderers/markdown.py` |
| `PdfRenderer` | Consumes `walk()` → reportlab PDF bytes (optional dep), span-based layout | `encino_rpt/renderers/pdf.py` |
| `JsonRenderer` | Serializes `ReportResult` to JSON with `schema_version` (`"1.0"`) | `encino_rpt/renderers/json.py` |
| `format_value`/`excel_number_format` | Shared value formatting per `Format` (currency, %, thousands, parens, dates) | `encino_rpt/renderers/_format.py` |
| `sanitize_csv`/`write_excel_cell`/`is_dangerous` | OWASP formula-injection mitigation for CSV/Excel output | `encino_rpt/renderers/_sanitize.py` |

## Pattern Overview

- **Fluent builder** returning `self` (or `Section`) for chaining; validation raises early (`encino_rpt/report.py`, `encino_rpt/section.py`).
- **Spec decoupling**: `*Spec` dataclasses (`encino_rpt/_specs.py`) record what the user declared; `build()` maps them to canonical `models.py` types that never appear in the builder.
- **Canonical tree is stdlib `@dataclass`** (NOT pydantic). The recursive `Group.children` union (`list[Detail | Group | Chart | Pivot]`) is resolved at deserialization time by a `type` discriminator dispatch map (`_NODES` in `encino_rpt/_serialize.py:22-27`).
- **Three-phase aggregation**: base totals computed per group (phase A), deferred expressions using `TOTAL("seccion.nombre")` resolved after the registry is complete (phase B, `encino_rpt/aggregation.py:494-507`), then `order_by`/`top(n)`/`suppress_zero` applied (phase C, `encino_rpt/aggregation.py:373-401`) before charts/pivots are appended.
- **Shared iterative `walk()` generator** centralizes the visitor traversal that every renderer consumes (`encino_rpt/renderers/_walk.py`).
- **Streaming renderers**: each renderer exposes `render()` (materialized) + `iter_*` (generator) + `write(result, file)`; `ReportResult` mirrors this with `to_*`/`render_*` (and `file=` params) plus `iter_*` convenience methods (`encino_rpt/models.py:224-439`).
- **Lazy imports** for all optional renderer dependencies (`openpyxl`, `reportlab`) and for the engine (`aggregation`) / renderers / readers to break import cycles.
- **In-memory aggregation engine**; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).
- **Module-level dispatch dicts** (`_BINOPS`, `_CMP`, `_OPS`, `_COLOR_OPS`, `_FORMAT_BY_EXT`) instead of if/else chains.

## Layers

### Declarative Layer

- Purpose: Declarative configuration of a report plus multi-format input.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`, `encino_rpt/readers.py`.
- Contains: The `Report` builder, the `Section` facade, internal `*Spec` dataclasses, and the `Reader` protocol + registry.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints), and lazily on `encino_rpt/readers.py` (inside `Report.read`) and `encino_rpt/aggregation.py` (inside `Report.run`).
- Used by: application code (see `README.md` examples).

### Engine Layer

- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (helpers `encino_rpt/expressions.py`, `encino_rpt/template.py`, `encino_rpt/charts.py`, `encino_rpt/pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, `_partition`, `_build_group_tree`, `_build_group`, `_build_instance`, `_build_path_group`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_render_templates`, `_build_kpis`.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:426-434`).

### Model Layer

- Purpose: Typed, JSON-serializable representation of the report result.
- Location: `encino_rpt/models.py` (13 dataclasses) + `encino_rpt/_serialize.py`.
- Depends on: stdlib only (`dataclasses`, `typing`, `datetime`, `decimal`, `enum`).
- Used by: the engine (writes), the renderers (read), and downstream consumers (`to_dict()` / `from_dict()` / `to_json()` / `from_json()`).

### Renderer Layer

- Purpose: Convert the canonical tree to a concrete output format.
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `markdown.py`, `_walk.py`, `_format.py`, `_sanitize.py`).
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras).
- Used by: `ReportResult` convenience methods and end users.

## Data Flow

### Primary Request Path (build a report)

### Secondary Flow (read → report)

### Render Flow

- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:29-42`); no module-level mutable state except the reader registry (`_READERS` in `encino_rpt/readers.py:35`).
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`encino_rpt/aggregation.py:591-604`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl`, set as plain instance attrs in `Group.__post_init__` (`encino_rpt/models.py:153-159`), replicating the former pydantic `PrivateAttr`.
- A fresh `Report` instance is required per report — `run()` does not reset the builder.

## Key Abstractions

### `ReportResult` (canonical contract)

- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:170-439`.
- Pattern: stdlib `@dataclass` with `root: Group` plus `meta`, `columns`, `formats`, `styles`, `kpis`; convenience render methods with lazy imports; `to_dict`/`from_dict`/`from_json` for round-trip.
- Serialization: `to_dict()` → `to_jsonable(self)`; `from_dict(data)` → `_build(ReportResult, data)` (round-trip verified in `tests/test_report.py`).

### `GroupSpec` + `Section` (builder spec + facade)

- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:76-93`, `encino_rpt/section.py:8-210`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`encino_rpt/report.py:360-424`).

### Expression evaluator (`evaluate`)

- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:55-123`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `encino_rpt/expressions.py:67-123`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`encino_rpt/expressions.py:46-48`).

### `walk()` (shared traversal)

- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py:8-31`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)` + `iter_*`/`write(result, file)`; register it in `encino_rpt/renderers/__init__.py`.

### `Reader` protocol + registry

- Purpose: Multi-format input to `list[dict]`, decoupled from `Report`.
- Location: `encino_rpt/readers.py`.
- Pattern: `Reader` is a `typing.Protocol` with `read(source, **opts) -> list[dict]`; `register_reader(name, reader)` mutates the module-level `_READERS` dict; `read()` resolves the name via `_resolve_format` (explicit `format=` or file extension) and dispatches through `get_reader()`. Six built-in readers are registered at import (`encino_rpt/readers.py:375-380`).
- Extension: `Report.register_reader(name, reader)` (`encino_rpt/report.py:80-90`) delegates here; custom readers are any object with a `read(source, **opts)` method.

### Path trie (`_PathNode`)

- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:270-331` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

### Public package API

- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, Reader, ...`.
- Responsibilities: re-export the builder, canonical model types, and `Reader` protocol; `__all__` lists 15 public names (`encino_rpt/__init__.py:21-37`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).

### `Report.run()`

- Location: `encino_rpt/report.py:426-434`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.

### `Report.read()` / `Report.register_reader()`

- Location: `encino_rpt/report.py:44-90`.
- Triggers: user call to build a `Report` from a file/file-like/raw source, or to register a custom reader.
- Responsibilities: delegate to `encino_rpt/readers.py`.

### `ReportResult` render methods

- Location: `encino_rpt/models.py:224-439` (`render_html`, `to_csv`, `to_text`, `to_markdown`, `to_excel`, `to_json`, `to_pdf`, plus `iter_html`/`iter_csv`/`iter_text`/`iter_markdown`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

### `readers.read()`

- Location: `encino_rpt/readers.py:350-371`.
- Triggers: `Report.read()` or direct `from encino_rpt.readers import read`.
- Responsibilities: resolve the reader name and dispatch to the reader's `read()`.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async. The reader registry `_READERS` (`encino_rpt/readers.py:35`) is the only module-level mutable state, and it is write-once-at-import plus user `register_reader` calls.
- **Global state:** `ExcelRenderer` stores transient mutable state on `self` (`_ws`, `_result`, `_formulas`, `_row` — `encino_rpt/renderers/excel.py:51-54`), making it non-reentrant across concurrent renders of the same instance. `PdfRenderer` sets `self._normal` during `render` (`encino_rpt/renderers/pdf.py:51`).
- **Circular imports:** Avoided via lazy imports. `report.py` imports `aggregation.py` lazily inside `run()` (`encino_rpt/report.py:432`) and `readers.py` lazily inside `read()`/`register_reader()` (`encino_rpt/report.py:75,88`); `models.py` imports renderers lazily inside convenience methods (`encino_rpt/models.py:224-437`) and `_serialize` lazily inside `to_dict`/`from_dict`. `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`encino_rpt/expressions.py`). `ast.parse` node/depth/pow counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:40-46`) and `ExcelReader.read` (`encino_rpt/readers.py:295-300`); `reportlab` only inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:35-48`). All raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **No pydantic at runtime:** The model layer is stdlib `@dataclass`; serialization is hand-rolled in `encino_rpt/_serialize.py`. The recursive `Group.children` union is deserialized via the `_NODES` discriminator map keyed on each node's `type` field (`encino_rpt/_serialize.py:22-27`).
- **Security posture:** OWASP formula-injection sanitization on CSV/Excel cells (`encino_rpt/renderers/_sanitize.py`); HTML attribute/value whitelisting against CSS injection (`encino_rpt/renderers/html.py:22-23`).

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

### Charts/pivots appended after phase-C ordering

### Duplicated operator/conditional tables per renderer

### Per-renderer event-handling duplication around `walk()`

## Error Handling

- **Builder validation:** `group()` raises `ValueError` when `columns` and `path` are both set (`encino_rpt/report.py:388-389`) and on duplicate cut names (`report.py:390-391`); `section()` raises `KeyError` for undeclared cuts (`report.py:421-423`); `Section.order_by` raises `ValueError` for invalid direction (`encino_rpt/section.py:163-164`).
- **Reader errors:** `get_reader()` raises `ValueError` for unregistered readers (`encino_rpt/readers.py:60-63`); `read()` raises `ValueError` when the format can't be resolved (`readers.py:347`); `TuplesReader` raises `ValueError` when `columns` is missing or mismatched (`readers.py:264-273`); JSON/JSONL readers raise `TypeError` for non-list/non-dict payloads.
- **Engine context wrapping:** `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:35-44`).
- **Expression errors:** `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`encino_rpt/expressions.py:51-123`).
- **Template errors:** `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`encino_rpt/template.py:20-32`).
- **Aggregate errors:** `ValueError` for unknown operators (`encino_rpt/aggregation.py:69`); `AggregationError` for unregistered custom aggregates (`aggregation.py:87`, `575`).
- **Optional dependency errors:** `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:43-46`, `renderers/pdf.py:45-48`, `readers.py:297-300`) — covered by `pytest.importorskip` in tests.
- **Serialization errors:** `JsonRenderer.render`/`to_dict` and `from_dict` convert deep-recursion `RecursionError` into a controlled `ValueError` (`renderers/json.py:29-41`, `_serialize.py:43-46`, `_serialize.py:126-129`).
- **Aggregation never catches exceptions:** a failing expression propagates up through `run()` to the caller.

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:strategy-start source:STRATEGY.md -->

## GSD Strategy

Estrategia híbrida "triage por riesgo" (detalle en `.planning/STRATEGY.md`):

1. **Nunca saltes el análisis**: `map-codebase` (CONCERNS) antes de decidir qué hacer; `code-review` + `verifier` al terminar.
2. **Ceremonia completa sólo con ambigüedad/riesgo** (feature nueva, refactor transversal, seguridad, infra/CI) → `/gsd-execute-phase`. Trabajo mecánico bien entendido → implementación directa.
3. **Reconciliación obligatoria tras trabajo directo**: sincronizar `.planning/ROADMAP.md`, `STATE.md` y `PROJECT.md` (o vía `/gsd-quick`).

<!-- GSD:strategy-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
