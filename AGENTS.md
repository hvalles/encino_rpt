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

- Python `>=3.10` — the entire library is pure Python. Configured in `pyproject.toml` (`requires-python = ">=3.10"`, line 13). Classifiers declare support for 3.10–3.13 (`pyproject.toml` lines 24–28).
- None detected. No TypeScript/JS, no compiled extensions. HTML output is generated as strings inside `encino_rpt/renderers/html.py` (not templated files).

## Runtime

- CPython only. This is a **library**, not an application/server — there is no server runtime, no web framework, no worker process. Local dev venv at `.venv/` (gitignored). CI runs on `ubuntu-latest` with Python 3.10/3.11/3.12/3.13 (`.github/workflows/ci.yml` lines 10–13). No `.python-version` or `.nvmrc` file present.
- `uv` — lockfile `uv.lock` (version 1) at repo root. All 49 dependency versions are pinned there.
- Lockfile: present (`uv.lock`).

## Frameworks

- **pydantic** `2.13.5` — canonical report data model (`ReportResult`, `Group`, `Total`, `Chart`, `Pivot`, `Kpi`, etc.) in `encino_rpt/models.py`. Declared `pydantic>=2` in `pyproject.toml` line 33 (the **only** runtime dependency). Used for validation and JSON serialization (`model_dump(mode="json")` in `encino_rpt/renderers/json.py:27`).
- **pytest** `9.1.1` — dev dependency (`pyproject.toml` lines 49–54, `pytest>=9.1.1`). Config in `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["."]` (`pyproject.toml` lines 44–46).
- Test files: `tests/test_report.py`, `tests/test_report_renderers.py`, `tests/test_security.py`.
- **hatchling** — build backend declared in `pyproject.toml` `[build-system]` (lines 1–3). Wheel packages `["encino_rpt"]` (`pyproject.toml` line 6).
- **ruff** `0.16.7` — linter, dev dependency (`pyproject.toml` line 53). NO config section (`[tool.ruff]`) and no `ruff.toml`/`.ruff.toml` — runs with defaults via `uv run ruff check` in CI (`.github/workflows/ci.yml` line 30).
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs dependency group, `pyproject.toml` lines 55–59), configured in `mkdocs.yml`.

## Key Dependencies

- **pydantic** `2.13.5` (`pydantic-core` `2.46.5`) — the entire data model in `encino_rpt/models.py` is pydantic v2 (`BaseModel`, `Field`, `PrivateAttr`, `Literal`). The recursive `Group.children` reference is resolved with `Group.model_rebuild()` (`encino_rpt/models.py:230`). Removing it would require rewriting the model layer.
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml` line 37). Imported lazily inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:42-46`): `Workbook`, `Font` (plus `get_column_letter`, chart classes and `styles.Font` imported per-method). Raises `ImportError` with a Spanish hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml` line 38). Imported lazily inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:30-41`): `colors`, `pagesizes.A4`, `styles.getSampleStyleSheet`, `platypus` (`Paragraph`, `SimpleDocTemplate`, `Table`, `TableStyle`). Same guarded-import pattern.
- **pillow** `12.3.0` — pulled in by the docs/render toolchain (mkdocs-material), not used directly.
- **requests** / **urllib3** / **certifi** / **idna** / **charset-normalizer** — transitive dependencies of the mkdocs docs toolchain (ghp-import, mkdocs), present in `uv.lock` but never imported by the library itself.
- **jinja2** / **markdown** / **pygments** / **pymdown-extensions** / **babel** — mkdocs/mkdocs-material transitive deps.

## Configuration

- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required. `.env` is listed in `.gitignore` (line 23) but no such file exists.
- `pyproject.toml` — hatchling build config, wheel packages `encino_rpt`.
- `mkdocs.yml` — docs config (material theme, `language: es`, mkdocstrings handler with `docstring_style: google`, 5-page nav).
- `.github/workflows/ci.yml`, `.github/workflows/docs.yml`, `.github/workflows/publish.yml` — CI/docs/publish pipelines.
- Existing built artifacts in `dist/`: `encino_rpt-0.2.0-py3-none-any.whl` and `encino_rpt-0.2.0.tar.gz` (gitignored; version 0.2.0, behind the current `version = "0.2.1"` in `pyproject.toml` line 10). Deploy via GitHub Actions only: `uv build` in `.github/workflows/publish.yml` line 19.

## Platform Requirements

- Python 3.10+ installed via `uv python install` (see `.github/workflows/ci.yml` line 21).
- `uv sync --all-extras --group dev` installs the full dev environment (`uv.lock`, `.github/workflows/ci.yml` line 24).
- `uv run pytest` runs the suite; `uv run ruff check` lints.
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml` to TestPyPI (main branch) and PyPI (tags `v*`). No hosting/deployment of an app — this is a library.
- Windows local dev (this repo lives on `win32`) but CI runs Linux; no OS-specific code detected in `encino_rpt/` (pure stdlib + pydantic).

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`
- Leading-underscore for internal modules: `_specs.py` (builder dataclasses), `renderers/_format.py`, `renderers/_sanitize.py`, `renderers/_walk.py` (shared traversal)
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`
- `PascalCase`: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`, `FieldSpec`, `ExpressionError`, `AggregationError`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`, `build_pivot`, `render`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_wrap`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_make_path_node`
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the only cross-module abbreviations
- `snake_case`: `rows`, `visible_set`, `child_pairs`, `deferred`, `registry`, `children_map`
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._groups` (`encino_rpt/report.py:27-39`), `self._spec` (`encino_rpt/section.py:11-12`)
- Pydantic `PrivateAttr` for non-serialized context: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:124-126`)
- Instance-private attributes set transiently by `ExcelRenderer.render` (not in `__init__`): `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:51-54`)
- `UPPER_SNAKE`, module-level, usually private: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:45-47`), `_TOKEN` regex (`encino_rpt/template.py:7`), `_DANGEROUS_PREFIXES`, `_LEADING_TRIM` (`encino_rpt/renderers/_sanitize.py:7-9`), `_SAFE_PROP`, `_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:21-22`), `SCHEMA_VERSION = "1.0"` (`encino_rpt/renderers/json.py:7`)
- Private module-level dispatch dicts map operator/type keys to lambdas: `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`encino_rpt/expressions.py:9-42`), `_OPS` (`encino_rpt/renderers/html.py:12-19`), `_COLOR_OPS` (`encino_rpt/renderers/excel.py:10-17`)
- Prefer `str | None` over `Optional[str]`; PEP 604 unions and builtin generics (`list[dict]`, `dict[str, Any]`) everywhere, enabled by `from __future__ import annotations`
- `Any` used for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`

## Code Style

- No formatter configured — no `black`, no `ruff format`. There is **no ruff config** (`pyproject.toml` has no `[tool.ruff]`, no `ruff.toml`/`.ruff.toml`).
- Linting only: **ruff** `0.16.7` (dev dependency, `pyproject.toml:53`), run with defaults via `uv run ruff check` (`.github/workflows/ci.yml:29-30`).
- Only rule set: ruff defaults. No `select`/`ignore` pinned. The suite is currently clean (`ruff check` exits 0).
- Indentation: 4 spaces throughout. Line length is not enforced.
- One known outlier: `encino_rpt/__init__.py:3-17` aligns `from .models import (...)` items to column 21, inconsistent with `encino_rpt/renderers/__init__.py` which uses one-item-per-line at 4-space indent.

## Import Organization

- `encino_rpt/models.py:3-7`: future import → `typing` (stdlib) → `pydantic`
- `encino_rpt/aggregation.py:3-20`: future import → blank → relative imports grouped alphabetically
- `from ._specs import ...` (`encino_rpt/report.py:7`)
- `from ..models import ...` (`encino_rpt/renderers/csv.py:8`)
- `from ._walk import walk` (`encino_rpt/renderers/csv.py:11`)
- `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:286`)
- `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html` (`encino_rpt/models.py:160`)
- `from openpyxl import Workbook` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:42-44`)
- `from reportlab.platypus import ...` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:30-39`)
- Per-helper imports: `from openpyxl.styles import Font` inside `_full_row`/`_total_row`/`_apply_conditional` (`encino_rpt/renderers/excel.py:161,170,188`)

## Error Handling

- `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:50`)
- `class AggregationError(ValueError)` (`encino_rpt/aggregation.py:23`)
- `ValueError` for invalid config: `raise ValueError(f"corte ya declarado: {name!r}")` (`encino_rpt/report.py:250`)
- `KeyError` for unknown named lookups: `f"corte no declarado: {name!r}"` (`encino_rpt/report.py:277`)
- `IndexError` for out-of-range param access: `f"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:26`)
- `AggregationError` wraps engine failures with context: `f"total {ts.name or ts.operator!r} (grupo {spec.name!r})"` (`encino_rpt/aggregation.py:195`)
- `raise ImportError("openpyxl no está instalado; instala el extra `excel`") from exc` (`encino_rpt/renderers/excel.py:46`)
- `raise ImportError("reportlab no está instalado; instala el extra `pdf`") from exc` (`encino_rpt/renderers/pdf.py:41`)
- Both guarded with `# pragma: no cover - depende del entorno` (`excel.py:45`, `pdf.py:40`)

## Logging

- No logging framework used — the library is pure and stateless, so no `logging` module anywhere. Errors are raised, not logged.

## Comments

- Module docstring in every module (one line, Spanish): `"""Agregación: enriquece renglones, construye el árbol de grupos y resuelve totales."""` (`encino_rpt/aggregation.py:1`)
- Google-style docstrings (Spanish) on every public class and method with `Args:`, `Returns:`, `Raises:` sections — see `Report.group` (`encino_rpt/report.py:224-246`) and `ReportResult.to_excel` (`encino_rpt/models.py:187-200`)
- Section banner comments inside longer modules: `# --- funciones / campos ---` (`encino_rpt/report.py:41`), `# --- árbol de grupos ---` (`encino_rpt/aggregation.py:138`), `# --- fase B ---` (`encino_rpt/aggregation.py:381`), `# --- plantillas (fase final) ---` (`encino_rpt/aggregation.py:392`)
- Inline comments explain non-obvious invariants, in Spanish: `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:80`), `# children: subgrupos o detalle` (`encino_rpt/aggregation.py:288`), `# Contexto interno (no serializado)...` (`encino_rpt/models.py:123`)
- Comments in source are **Spanish**; avoid English comments in new code.

## Function Design

- `def set_format(self, column: str, *, kind: str = "number", ...)` (`encino_rpt/report.py:68-72`)
- `def add_field(self, name: str, expression: str | None = None, *, after: str | None = None, ...)` (`encino_rpt/report.py:145-148`)

## Module Design

- Public fluent facade: `encino_rpt/report.py` (`Report`) + `encino_rpt/section.py` (`Section`) — mutate internal spec dataclasses
- Internal specs: `encino_rpt/_specs.py` (dataclasses, `field(default_factory=list)` for mutable defaults)
- Canonical output model: `encino_rpt/models.py` (pydantic `BaseModel`, `Field(default_factory=...)` for mutable defaults, `PrivateAttr` for non-serialized context)
- Pipeline: `encino_rpt/aggregation.py` → `charts.py` / `pivot.py` / `expressions.py` / `template.py`
- Renderers: `encino_rpt/renderers/` — consume the shared `walk` generator and dispatch per event

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

### `.__init__.py` import-list alignment

### Cross-module private attribute access

### Duplicated operator/conditional tables per renderer

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs, custom functions/aggregates | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a group's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress/page_break) | `encino_rpt/section.py` |
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

- Fluent builder API returning `self` for chaining (`report.py`, `section.py`).
- Spec objects (`_specs.py`) decouple what the user declared from the canonical output.
- Two-phase total resolution: base totals first, then deferred expressions using `TOTAL("seccion.nombre")` (phase B in `aggregation.py:382-389`).
- Post-processing phase C: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed, before charts/pivots are appended (`aggregation.py:304,321-331`).
- Pydantic v2 models with typed discriminators (`type: Literal[...]`) for polymorphic children.
- Shared iterative `walk()` generator centralizes the visitor traversal that each renderer previously duplicated (`encino_rpt/renderers/_walk.py`).
- Lazy imports for all optional renderer dependencies (`openpyxl`, `reportlab`) and even required internal modules to break import cycles.
- In-memory aggregation engine; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).

## Layers

- Purpose: Declarative configuration of a report.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`.
- Contains: The `Report` builder, the `Section` facade, and internal `*Spec` dataclasses.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints).
- Used by: application code (see README examples).
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (with helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, partitioning, group-tree construction, total computation, deferred resolution, template resolution, KPI computation.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:280-288`).
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

- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:27-39`); there is no module-level mutable state.
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:466-473`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl` via pydantic `PrivateAttr` (`encino_rpt/models.py:123-126`).
- A fresh `Report` instance is required per report — `run()` does not reset the builder, so re-running `run()` re-executes the full aggregation.

## Key Abstractions

- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:136-228`.
- Pattern: pydantic `BaseModel` with typed children (`root: Group`), convenience render methods with lazy imports, `to_json` with `schema_version`.
- Serialization: `model_dump()` / `model_validate()` round-trip verified in `tests/test_report.py`.
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:77-96`, `encino_rpt/section.py`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`report.py:224-278`).
- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:54-63`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:66-118`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:45-47`).
- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)`; register it in `encino_rpt/renderers/__init__.py`.
- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:214-274` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, ...`.
- Responsibilities: re-export the builder and canonical model types; `__all__` lists 14 public names (`__init__.py:20-34`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).
- Location: `encino_rpt/report.py:280-288`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.
- Location: `encino_rpt/models.py:150-227` (`render_html`, `to_csv`, `to_text`, `to_excel`, `to_json`, `to_pdf`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async, no shared state outside the `Report` instance. Engine helpers in `aggregation.py` are module-level functions with private `_`-prefixed names.
- **Global state:** None at module level. All mutable state is per-`Report` instance or local to `build()`.
- **Circular imports:** Avoided. `report.py` imports `aggregation.py` lazily inside `run()` (`report.py:286`); `models.py` imports renderers lazily inside convenience methods (`models.py:160-227`). `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`expressions.py`). `ast.parse` node/depth counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`renderers/excel.py:42-46`); `reportlab` only inside `PdfRenderer.render` (`renderers/pdf.py:30-41`). Both raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **Pydantic forward references:** `Group.children` is a recursive union, resolved with `Group.model_rebuild()` at the bottom of `encino_rpt/models.py:230`.

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

### Charts/pivots appended after phase-C ordering

### Duplicated operator/format tables per renderer

## Error Handling

- Builder validation: `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:247-248`) and on duplicate cut names (`report.py:249-250`); `section()` raises `KeyError` for undeclared cuts (`report.py:275-277`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:130-131`).
- Engine context wrapping: `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`aggregation.py:27-36`).
- Expression errors: `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`expressions.py:50-118`).
- Template errors: `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`template.py:23-29`).
- Aggregate errors: `ValueError` for unknown operators (`aggregation.py:61`); `AggregationError` for unregistered custom aggregates (`aggregation.py:69,452`).
- Optional dependency errors: `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:46`, `renderers/pdf.py:41`) — covered by `pytest.importorskip` in tests.
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
