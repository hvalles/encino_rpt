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

- Python `>=3.10` — the entire library is pure Python. Declared via `requires-python = ">=3.10"` in `pyproject.toml:13`. Classifiers declare support for 3.10–3.13 (`pyproject.toml:25-28`). No compiled extensions.
- None detected. No TypeScript/JS, no templated files. HTML output is generated as strings inside `encino_rpt/renderers/html.py`. Markdown is used only for docs (`docs/*.md`).

## Runtime

- CPython only. This is a **library**, not an application/server — no server runtime, no web framework, no worker process. Local dev venv at `.venv/` (gitignored). CI runs on `ubuntu-latest`.
- `uv` (Astral). Lockfile `uv.lock` (lockfile version 1) at repo root. All dependency versions are pinned there. No `requirements.txt`, `pyproject`-only.
- Lockfile: present (`uv.lock`, ~338 KB).

## Frameworks

- **pydantic** `2.13.5` (`pydantic-core` `2.46.5`) — canonical report data model (`ReportResult`, `Group`, `Total`, `Chart`, `Pivot`, `Kpi`, etc.) in `encino_rpt/models.py`. Declared `pydantic>=2` in `pyproject.toml:33` — the **only** runtime dependency. Used for validation and JSON serialization (`model_dump(mode="json")` in `encino_rpt/renderers/json.py:27`).
- **pytest** `9.1.1` — dev group (`pyproject.toml:50`, `pytest>=9.1.1`). Config `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `pythonpath = ["."]` (`pyproject.toml:44-46`).
- **pytest-cov** `7.1.0` — dev group (`pyproject.toml:55`). Backed by **coverage** `7.16.1` (transitive). Enforced in the CI `quality` job via `--cov-fail-under=80` (`.github/workflows/ci.yml:53`).
- **mypy** `2.3.1` — dev group (`pyproject.toml:54`). Config `[tool.mypy]` (`pyproject.toml:63-71`): `plugins = ["pydantic.mypy"]`, `python_version = "3.10"`, `check_untyped_defs`, `warn_unused_ignores`, `warn_redundant_casts`, `no_implicit_optional`, and `disable_error_code = ["import-untyped"]` (openpyxl/reportlab have no typed stubs).
- **hatchling** — build backend declared in `[build-system]` (`pyproject.toml:1-3`). Wheel packages `["encino_rpt"]` (`pyproject.toml:6`). Not version-pinned in `uv.lock` (build backend, not a project dependency).
- **ruff** `0.16.7` — linter + formatter, dev group (`pyproject.toml:53`). Config now present: `[tool.ruff]` (`pyproject.toml:73-76`) sets `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`; `[tool.ruff.format]` (`pyproject.toml:78-79`) sets `quote-style = "double"`.
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs group, `pyproject.toml:58-60`), configured in `mkdocs.yml`.

## Key Dependencies

- **pydantic** `2.13.5` — the entire data model in `encino_rpt/models.py` is pydantic v2 (`BaseModel`, `Field`, `PrivateAttr`, `Literal`). The recursive `Group.children` reference is resolved with `Group.model_rebuild()` (`encino_rpt/models.py:232`). Removing it would require rewriting the model layer.
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml:37`). Imported lazily inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py`). Raises `ImportError` with a Spanish hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml:38`). Imported lazily inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py`). Same guarded-import pattern.
- **pillow** `12.3.0` — pulled in by mkdocs-material.
- **requests** / **urllib3** / **certifi** / **idna** / **charset-normalizer** — transitive deps of mkdocs (ghp-import). Never imported by `encino_rpt/` (verified: no network imports anywhere in the package).
- **jinja2** / **markdown** / **pygments** / **pymdown-extensions** / **babel** — mkdocs/mkdocs-material transitive deps.

## Configuration

- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required. `.env` is listed in `.gitignore:23` but no such file exists. Secrets for publishing live only in GitHub Actions (`TEST_PYPI_API_TOKEN`, `PYPI_API_TOKEN`).
- `pyproject.toml` — hatchling build config, project metadata, dependency groups, and tool configs for pytest/mypy/ruff/coverage.
- `mkdocs.yml` — docs config (material theme, `language: es`, mkdocstrings handler with `docstring_style: google`, 5-page nav).
- `.github/workflows/ci.yml` — CI with two jobs: `test` (matrix 3.10–3.13) and `quality` (singleton 3.13).
- `.github/workflows/docs.yml` — builds docs and deploys to GitHub Pages.
- `.github/workflows/publish.yml` — builds wheel/sdist and publishes to TestPyPI (main) and PyPI (tags `v*`).
- Existing built artifacts in `dist/`: `encino_rpt-0.2.0-py3-none-any.whl` and `encino_rpt-0.2.0.tar.gz` (gitignored; version 0.2.0, behind the current `version = "0.2.1"` in `pyproject.toml:10`). Deploy via GitHub Actions only: `uv build` in `.github/workflows/publish.yml:19`.

## Platform Requirements

- Python 3.10+ installed via `uv python install` (`.github/workflows/ci.yml:21`).
- `uv sync --all-extras --group dev` installs the full dev environment (`.github/workflows/ci.yml:24`).
- `uv run pytest` runs the suite; `uv run ruff check` lints; `uv run ruff format --check encino_rpt tests` checks formatting; `uv run mypy encino_rpt` type-checks; `uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80` enforces ≥80% coverage.
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml`. Docs hosted on GitHub Pages (`https://hvalles.github.io/encino_rpt/`). No application hosting — this is a library.
- Windows local dev (this repo lives on `win32`) but CI runs Linux; no OS-specific code detected in `encino_rpt/` (pure stdlib + pydantic).

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`
- Leading underscore for internal modules: `encino_rpt/_specs.py` (builder dataclasses), `encino_rpt/renderers/_format.py`, `encino_rpt/renderers/_sanitize.py`, `encino_rpt/renderers/_walk.py`
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_perf_smoke.py`
- `PascalCase`: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`, `FieldSpec`, `ExpressionError`, `AggregationError`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)
- Internal helper class `_PathNode` (trie node) prefixed `_` (`encino_rpt/aggregation.py:246`)
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`, `build_pivot`, `render`, `build`, `walk`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_wrap`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_make_path_node`, `_walk`, `_full_row`, `_total_row`, `_cell_attrs`, `_style_attr`, `_add_thousands`
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the only cross-module abbreviations
- `snake_case`: `rows`, `visible_set`, `child_pairs`, `deferred`, `registry`, `children_map`, `root_spec`, `spec`
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._groups`, `self._fields`, `self._detail`, `self._order`, `self._formats`, `self._styles`, `self._datasets`, `self._kpis`, `self._aggregates` (`encino_rpt/report.py:29-41`), `self._spec` (`encino_rpt/section.py:11-12`)
- Pydantic `PrivateAttr` for non-serialized context: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:124-126`)
- Instance-private attributes set transiently by `ExcelRenderer.render` (not in `__init__`): `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:55-58`)
- `UPPER_SNAKE`, module-level: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:46-48`), `_TOKEN` regex (`encino_rpt/template.py:7`), `_DANGEROUS_PREFIXES`, `_LEADING_TRIM` (`encino_rpt/renderers/_sanitize.py:7-9`), `_SAFE_PROP`, `_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:21-22`), `SCHEMA_VERSION = "1.0"` (`encino_rpt/renderers/json.py:7`)
- `from __future__ import annotations` at the top of every module (enables PEP 604 unions and builtin generics)
- Prefer `str | None` over `Optional[str]`; builtin generics (`list[dict]`, `dict[str, Any]`) everywhere
- `Any` used for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`

## Code Style

- **ruff** `0.16.7` — formatter is now configured via `[tool.ruff.format]` in `pyproject.toml:78-79` with `quote-style = "double"`
- `[tool.ruff]` config (`pyproject.toml:73-76`): `target-version = "py310"`, `line-length = 88`, `extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`
- Line length is 88 (enforced by ruff format check in CI, `.github/workflows/ci.yml:50`)
- Indentation: 4 spaces throughout
- Double quotes for strings (ruff format `quote-style = "double"`)
- **ruff** `0.16.7` (dev dependency, `pyproject.toml:53`), run with defaults: `uv run ruff check` (`.github/workflows/ci.yml:30`). No `select`/`ignore` pinned — ruff defaults only.
- **mypy** `2.3.1` (dev dependency, `pyproject.toml:54`), configured in `[tool.mypy]` (`pyproject.toml:63-71`):
- Run in CI as `uv run mypy encino_rpt` (`.github/workflows/ci.yml:47`)

## Import Organization

- `encino_rpt/models.py:3-7`: future import → `typing` (stdlib) → `pydantic`
- `encino_rpt/aggregation.py:3-24`: future import → `typing` → blank → relative imports grouped alphabetically (`_specs`, `charts`, `expressions`, `models`, `pivot`, `template`)
- `from ._specs import FieldSpec, GroupSpec, KpiSpec` (`encino_rpt/report.py:7`)
- `from ..models import Image, Link` (`encino_rpt/renderers/csv.py:8`)
- `from ._walk import walk` (`encino_rpt/renderers/csv.py:11`)
- `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:367`)
- `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html` (`encino_rpt/models.py:162`); same pattern for csv/text/excel/json/pdf (`models.py:175,185,200,213,227`)
- `from openpyxl import Workbook` + `from openpyxl.styles import Font` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:44-46`)
- `from reportlab.platypus import ...` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:31-40`)
- Per-helper imports for optional deps: `from openpyxl.styles import Font` inside `_full_row`/`_total_row`/`_apply_conditional`/`_chart`/`_pivot` (`encino_rpt/renderers/excel.py:170,179,197,217,252`); `from reportlab.platypus import Paragraph` inside `pdf.py:125,137,143`

## Error Handling

- `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:51`)
- `class AggregationError(ValueError)` (`encino_rpt/aggregation.py:30`)
- `ValueError` for invalid config: `raise ValueError("`columns` y `path` son excluyentes")` (`encino_rpt/report.py:324`), `raise ValueError(f"corte ya declarado: {name!r}")` (`report.py:326`)
- `KeyError` for unknown named lookups: `f"corte no declarado: {name!r}"` (`encino_rpt/report.py:358`)
- `IndexError` for out-of-range param access: `f"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:26-28`)
- `ValueError` for invalid direction: `f"dirección de orden inválida: {direction!r}"` (`encino_rpt/section.py:172-173`)
- `_wrap(context, fn, *args)` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:34-43`). Used for field enrichment (`campo {name!r} (fila {index})`), totals (`total {name or operator!r} (grupo {spec.name!r})`), deferred totals, and KPIs.
- `raise ImportError("openpyxl no está instalado; instala el extra `excel`") from exc` (`encino_rpt/renderers/excel.py:47-50`)
- `raise ImportError("reportlab no está instalado; instala el extra `pdf`") from exc` (`encino_rpt/renderers/pdf.py:41-44`)
- Both branches marked `# pragma: no cover - depende del entorno` (excluded from coverage via `exclude_lines` in `pyproject.toml:88`)

## Logging

## Comments

- One-line module docstring in every module (Spanish): `"""Builder fluido `Report`."""` (`encino_rpt/report.py:1`), `"""Evaluador seguro de expresiones (sin `eval`, whitelist vía `ast`)."""` (`encino_rpt/expressions.py:1`)
- Google-style docstrings (Spanish) on every public class and method, with `Args:`, `Returns:`, `Raises:` sections — see `Report.group` (`encino_rpt/report.py:295-322`), `ReportResult.to_excel` (`encino_rpt/models.py:189-202`), `Report.set_format` (`report.py:70-98`)
- Renderer `render()` docstrings include a `Raises:` section documenting the `ImportError` for optional deps (`excel.py:41-42`, `pdf.py:28-29`)
- `# --- funciones / campos ---` (`encino_rpt/report.py:43`)
- `# --- detalle / grupos ---` (`report.py:281`)
- `# --- árbol de grupos ---` (`encino_rpt/aggregation.py:155`)
- `# --- fase B ---` (`aggregation.py:447`)
- `# --- plantillas (fase final) ---` (`aggregation.py:464`)
- `# --- P1: inyección de fórmulas ---` and similar in `tests/test_security.py`
- `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:80`)
- `# children: subgrupos o detalle` (`encino_rpt/aggregation.py:324`)
- `# Contexto interno (no serializado)...` (`encino_rpt/models.py:123`)
- `# fase C sobre los hijos (grupos/detalle), antes de añadir chart/pivot` (`aggregation.py:349`)
- `# dividir cada fila una sola vez (PERF-02)` (`aggregation.py:260`)

## Function Design

- Keyword-only parameters after `*` for optional config: `def set_format(self, column: str, *, kind: str = "number", ...)` (`encino_rpt/report.py:70-82`), `def add_field(self, name: str, expression: str | None = None, *, after: str | None = None, ...)` (`report.py:173-183`)
- Optional config params often untyped (`format=None`, `fn`) where the type is `Format`/callable — see `add_function(self, name: str, fn) -> Report` (`report.py:44`)
- Fluent builder methods always return `self` (or `Section`) for chaining, with `Returns:` docstring noting "El propio reporte (fluido)."

## Module Design

- `encino_rpt/__init__.py` re-exports 14 public names via `__all__` (`__init__.py:20-34`). `Section` is intentionally NOT exported (reachable only via `Report.group()`/`Report.section()`).
- `encino_rpt/renderers/__init__.py` exports the 6 renderer classes via `__all__` (`renderers/__init__.py:10-17`).
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

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs, custom functions/aggregates; `run()` materializes the tree | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a group's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress_zero/page_break) | `encino_rpt/section.py` |
| `FieldSpec`/`GroupSpec`/`TotalSpec`/`ChartSpec`/`PivotSpec`/`KpiSpec` | Internal builder specifications (dataclasses) — NOT part of the canonical tree | `encino_rpt/_specs.py` |
| `evaluate()` | Safe expression evaluator (AST whitelist, no `eval`, anti-DoS limits) | `encino_rpt/expressions.py` |
| `render()` | `{{token}}` template interpolation for header/footer and link/image URLs | `encino_rpt/template.py` |
| `build()` | Orchestrates `run()`: validate, visible columns, row enrichment, group tree construction, totals, deferred `TOTAL(...)` resolution, template rendering, KPIs → `ReportResult` | `encino_rpt/aggregation.py` |
| `build_chart()` | Derives `Chart.labels`/`series` from already-aggregated child groups or the group's own totals | `encino_rpt/charts.py` |
| `build_pivot()` | Builds a rows × columns cross-tab matrix (`Pivot`) with row/column totals | `encino_rpt/pivot.py` |
| Pydantic models | Canonical serializable tree: `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta` | `encino_rpt/models.py` |
| `walk()` | Shared iterative tree traversal; yields typed `(event, node)` tuples consumed by every renderer | `encino_rpt/renderers/_walk.py` |
| `HtmlRenderer` | Consumes `walk()` → HTML `<table>` with classes, conditional styles, pivot sub-tables | `encino_rpt/renderers/html.py` |
| `ExcelRenderer` | Consumes `walk()` → openpyxl `Worksheet` (optional dep), native charts, `=SUM(...)` formula mode, cell formatting | `encino_rpt/renderers/excel.py` |
| `CsvRenderer` | Consumes `walk()` → flattened CSV with formula-injection sanitization | `encino_rpt/renderers/csv.py` |
| `TextRenderer` | Consumes `walk()` → indented plain text for inspection | `encino_rpt/renderers/text.py` |
| `PdfRenderer` | Consumes `walk()` → reportlab PDF bytes (optional dep), span-based layout | `encino_rpt/renderers/pdf.py` |
| `JsonRenderer` | Serializes `ReportResult` to JSON with `schema_version` (`"1.0"`) | `encino_rpt/renderers/json.py` |
| `format_value`/`excel_number_format` | Shared value formatting per `Format` (currency, %, thousands, parens, dates) | `encino_rpt/renderers/_format.py` |
| `sanitize_csv`/`write_excel_cell`/`is_dangerous` | OWASP formula-injection mitigation for CSV/Excel output | `encino_rpt/renderers/_sanitize.py` |

## Pattern Overview

- Fluent builder API returning `self` for chaining (`report.py`, `section.py`); validation raises early (e.g. `group()` duplicate cut `report.py:325-326`).
- Spec objects (`_specs.py`) decouple what the user declared from the canonical output — specs are consumed by `build()` and never appear in the result tree.
- Two-phase total resolution: base totals first, then deferred expressions using `TOTAL("seccion.nombre")` (phase B in `aggregation.py:448-461`).
- Post-processing phase C: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed, before charts/pivots are appended (`aggregation.py:349-368`).
- Pydantic v2 models with typed discriminators (`type: Literal[...]`) for polymorphic children; the recursive `Group.children` union is resolved via `Group.model_rebuild()` (`models.py:232`).
- Shared iterative `walk()` generator centralizes the visitor traversal that each renderer previously duplicated (`renderers/_walk.py`).
- Lazy imports for all optional renderer dependencies (`openpyxl`, `reportlab`) and for the engine (`aggregation`) / renderers to break import cycles.
- In-memory aggregation engine; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).

## Layers

- Purpose: Declarative configuration of a report.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`.
- Contains: The `Report` builder, the `Section` facade, and internal `*Spec` dataclasses.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints).
- Used by: application code (see `README.md` examples).
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, `_partition`, `_build_group_tree`, `_build_group`, `_build_instance`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_render_templates`, `_build_kpis`.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:361-369`).
- Purpose: Typed, JSON-serializable representation of the report result.
- Location: `encino_rpt/models.py`.
- Contains: 13 pydantic models (see Component Responsibilities table).
- Depends on: `pydantic>=2` only.
- Used by: the engine (writes), the renderers (read), and downstream consumers (`model_dump()` / `model_validate()` / `to_json()`).
- Purpose: Convert the canonical tree to a concrete output format.
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `_walk.py`, `_format.py`, `_sanitize.py`).
- Contains: Visitor-style renderer classes + shared walker/formatting/sanitizing helpers.
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras).
- Used by: `ReportResult` convenience methods and end users.

## Data Flow

### Primary Request Path (build a report)

### Secondary Flow (render to a destination)

- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:29-41`); there is no module-level mutable state.
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:543-549`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl` via pydantic `PrivateAttr` (`encino_rpt/models.py:123-126`).
- A fresh `Report` instance is required per report — `run()` does not reset the builder, so re-running `run()` re-executes the full aggregation.

## Key Abstractions

- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:136-228`.
- Pattern: pydantic `BaseModel` with typed children (`root: Group`), convenience render methods with lazy imports, `to_json` with `schema_version`.
- Serialization: `model_dump()` / `model_validate()` round-trip verified in `tests/test_report.py`.
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:77-96`, `encino_rpt/section.py`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`report.py:295-359`).
- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:55-123`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:67-123`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:46-48`).
- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)`; register it in `encino_rpt/renderers/__init__.py`.
- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:246-307` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, ...`.
- Responsibilities: re-export the builder and canonical model types; `__all__` lists 14 public names (`__init__.py:20-34`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).
- Location: `encino_rpt/report.py:361-369`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.
- Location: `encino_rpt/models.py:150-229` (`render_html`, `to_csv`, `to_text`, `to_excel`, `to_json`, `to_pdf`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async, no shared state outside the `Report` instance. Engine helpers in `aggregation.py` are module-level functions with private `_`-prefixed names.
- **Global state:** None at module level. All mutable state is per-`Report` instance or local to `build()`. The `ExcelRenderer` stores transient mutable state on `self` (`_ws`, `_result`, `_formulas`, `_row` — `renderers/excel.py:55-58`), making it non-reentrant across concurrent renders of the same instance.
- **Circular imports:** Avoided. `report.py` imports `aggregation.py` lazily inside `run()` (`report.py:367`); `models.py` imports renderers lazily inside convenience methods (`models.py:162-227`). `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`expressions.py`). `ast.parse` node/depth counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`renderers/excel.py:44-46`); `reportlab` only inside `PdfRenderer.render` (`renderers/pdf.py:31-41`). Both raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **Pydantic forward references:** `Group.children` is a recursive union, resolved with `Group.model_rebuild()` at the bottom of `encino_rpt/models.py:232`.

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

### Charts/pivots appended after phase-C ordering

### Duplicated operator/conditional tables per renderer

### Reimplementing tree traversal per renderer

## Error Handling

- Builder validation: `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:323-324`) and on duplicate cut names (`report.py:325-326`); `section()` raises `KeyError` for undeclared cuts (`report.py:356-358`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:172-173`).
- Engine context wrapping: `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`aggregation.py:34-43`).
- Expression errors: `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`expressions.py:51-123`).
- Template errors: `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`template.py:20-31`).
- Aggregate errors: `ValueError` for unknown operators (`aggregation.py:68`); `AggregationError` for unregistered custom aggregates (`aggregation.py:76`, `528-529`).
- Optional dependency errors: `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:48-50`, `renderers/pdf.py:42-44`) — covered by `pytest.importorskip` in tests.
- Aggregation never catches exceptions: a failing expression propagates up through `run()` to the caller.

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
