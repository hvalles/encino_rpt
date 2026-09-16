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
- Python `>=3.10` — the entire library is pure Python (`encino_rpt/`). Configured in `pyproject.toml` (`requires-python = ">=3.10"`, line 13). Classifiers declare support for 3.10–3.13.
- None detected. No TypeScript/JS, HTML templates are generated as strings inside `encino_rpt/renderers/html.py` (not templated files).
## Runtime
- CPython. Local dev venv at `.venv/` (gitignored). CI runs on `ubuntu-latest` with Python 3.10/3.11/3.12/3.13 (`.github/workflows/ci.yml`). No `.python-version` or `.nvmrc` file present.
- Library outputs XLSX/PDF are produced at runtime by optional renderers only — no server runtime.
- `uv` — lockfile `uv.lock` (version 1) at repo root.
- Lockfile: present (`uv.lock`). All dependency versions below are pinned there.
## Frameworks
- **pydantic** `2.13.5` — canonical report data model (`ReportResult`, `Group`, `Total`, `Chart`, etc.) in `encino_rpt/models.py`. Declared `pydantic>=2` in `pyproject.toml` line 34. Used for validation and JSON serialization (`model_dump()`).
- **encino-orm** `0.2.6` — declared dependency (`encino-orm>=0.2.1`) but NOT imported anywhere in `encino_rpt/` or `tests/`. Companion package whose `fetch_all`/`fetch_many`/`paginate` output (`list[dict]`) is the library's input contract (per `README.md` and `docs/design/10-report.md`).
- **pytest** `9.1.1` — dev dependency (`pyproject.toml` line 52). Config in `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and `pythonpath = ["."]`.
- Test files: `tests/test_report.py`, `tests/test_report_renderers.py`, `tests/test_security.py`.
- **hatchling** — build backend declared in `pyproject.toml` `[build-system]` (line 2–3). Wheel packages `["encino_rpt"]`.
- **ruff** `0.16.7` — linter, dev dependency. NO config file detected (no `[tool.ruff]` section in `pyproject.toml`, no `ruff.toml`/`.ruff.toml`) — runs with defaults via `uv run ruff check` in CI.
- **mkdocs** `1.6.1` + **mkdocs-material** `9.7.7` + **mkdocstrings** `1.0.6` — docs toolchain (docs dependency group, `pyproject.toml` lines 56–59), configured in `mkdocs.yml`.
## Key Dependencies
- **pydantic** `2.13.5` (`pydantic-core` `2.46.5`) — the entire data model in `encino_rpt/models.py` is pydantic v2 (`BaseModel`, `Field`, `PrivateAttr`, `Literal` types). Removing it would require rewriting the model layer.
- **openpyxl** `3.1.5` — optional extra `excel` (`pyproject.toml` line 38). Imported lazily inside `encino_rpt/renderers/excel.py:41-45` (`Workbook`, `Font` from `openpyxl`). Raises `ImportError` with a hint to install `encino-rpt[excel]` when missing.
- **reportlab** `5.0.1` — optional extra `pdf` (`pyproject.toml` line 39). Imported lazily inside `encino_rpt/renderers/pdf.py:29-38` (`colors`, `pagesizes.A4`, `styles`, `platypus` — `Paragraph`, `SimpleDocTemplate`, `Table`, `TableStyle`). Same guarded-import pattern.
- **pillow** `12.3.0` — transitive dependency in `uv.lock` (pulled in by the docs/render toolchain), not directly used by `encino_rpt/`.
- **encino-orm** `0.2.6` pulls the following DB drivers transitively (see `uv.lock`): `aiomysql` 0.3.1, `aiosqlite` 0.22.1, `asyncpg` 0.31.0, `pymysql` 1.2.0. These are present because encino-orm supports multiple backends; `encino_rpt` itself never queries a database.
## Configuration
- Single source of truth: `pyproject.toml` (project metadata, dependencies, optional extras `excel`/`pdf`, dev/docs dependency groups, pytest options).
- No `.env`, `.env.*`, or env-var-driven config detected. The library is pure and stateless — no runtime environment variables required.
- Docs config separate: `mkdocs.yml` (site metadata, material theme, mkdocstrings handler with `docstring_style: google`, nav for 5 pages, markdown extensions).
- `pyproject.toml` — hatchling build config, wheel packages `encino_rpt`.
- Existing built artifacts in `dist/`: `encino_rpt-0.2.0-py3-none-any.whl` and `encino_rpt-0.2.0.tar.gz` (gitignored, version behind current 0.2.1).
- Deploy via GitHub Actions only: `uv build` in `.github/workflows/publish.yml`.
## Platform Requirements
- Python 3.10+ installed via `uv python install` (see `.github/workflows/ci.yml`).
- `uv sync --all-extras --group dev` installs the full dev environment (per CI).
- Windows local dev (this repo lives on `win32`), but CI runs Linux — no OS-specific code detected in `encino_rpt/` (pure stdlib + pydantic).
- Distributed as a PyPI package (`encino-rpt`), published via `.github/workflows/publish.yml` to TestPyPI (main branch) and PyPI (tags `v*`). No hosting/deployment of an app — this is a library.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Overview
## Naming Patterns
- `snake_case.py` for modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`
- Leading-underscore for internal modules: `_specs.py` (builder dataclasses), `renderers/_format.py`, `renderers/_sanitize.py`
- Leading-underscore for internal helpers: `renderers/_format.py`, `renderers/_sanitize.py`
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`
- PascalCase: `Report`, `Section`, `ReportResult`, `Group`, `HtmlRenderer`, `FieldSpec`, `ExpressionError`
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `PdfRenderer`, `TextRenderer` (in `encino_rpt/renderers/`)
- Spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (in `encino_rpt/_specs.py`)
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_walk`
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the only cross-module abbreviations
- `snake_case`: `rows`, `visible_set`, `child_pairs`, `deferred`
- Private instance attributes prefixed `_` and set in `__init__`:
- Pydantic `PrivateAttr` for non-serialized context: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:124-126`)
- `UPPER_SNAKE`, module-level, usually private: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:45-47`), `_TOKEN` regex (`encino_rpt/template.py:7`), `_DANGEROUS_PREFIXES` (`encino_rpt/renderers/_sanitize.py:5`)
- Private module-level constant dicts map operator strings to lambdas: `_OPS`, `_COLOR_OPS` (`encino_rpt/renderers/excel.py:9`, `encino_rpt/renderers/html.py:11`), `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`encino_rpt/expressions.py:9-42`)
- Prefer `str | None` over `Optional[str]`; PEP 604 unions and builtin generics (`list[dict]`, `dict[str, Any]`) everywhere, enabled by `from __future__ import annotations`
- `Any` used for untyped row data: `dict[str, Any]`, `value: Any`, `format: Any`
## Code Style
- No formatter (no black/ruff-format) and **no ruff config section** — CI runs `uv run ruff check` with defaults (`.github/workflows/ci.yml:29-30`)
- One notable outlier: `encino_rpt/__init__.py` aligns import-list items to column 21 inside `from .models import (...)`; ruff does not flag it but it is inconsistent with `encino_rpt/renderers/__init__.py`, which uses one-item-per-line at 4-space indent
- Ruff, installed as a dev dependency (`pyproject.toml:54`), version 0.16.7 in the lockfile
- Only rule set: ruff defaults. No `select`/`ignore` pinned. The suite is currently clean (verified `ruff check` exit 0)
- Order: `from __future__ import annotations` first, blank line, then stdlib, blank line, third-party, blank line, relative imports. Examples:
- Small internal security helper imported into renderers: `from ._sanitize import sanitize_csv` (`encino_rpt/renderers/csv.py:10`)
- No path aliases; all intra-package imports are relative (`from .`, `from ..`, `from .renderers.`)
## Import Organization
- None. Intra-package imports are always relative.
## Error Handling
- Define domain exceptions as subclasses of builtins: `class ExpressionError(ValueError)` (`encino_rpt/expressions.py:50`)
- `ExpressionError` raised for unknown names, disallowed operators, too-complex/deep expressions, oversized exponents, keyword args on calls (`encino_rpt/expressions.py:59,65,73,77,81,87,93,101,104,106,108,109`)
- `ValueError` for invalid config values, always with a Spanish message including the offending value via `!r`:
- `KeyError` for unknown named lookups: `f"corte no declarado: {name!r}"` (`encino_rpt/report.py:275`)
- `IndexError` for out-of-range param access: `f"parámetro {index} fuera de rango (hay {len(params)})"` (`encino_rpt/template.py:26`)
- Optional-dependency guards re-raise `ImportError` with `from exc` and a Spanish installation hint: `raise ImportError("openpyxl no está instalado; instala el extra `excel`") from exc` (`encino_rpt/renderers/excel.py:45`, `encino_rpt/renderers/pdf.py:40`)
## Logging
## Comments
- Module docstring in every module (one line, Spanish): `"""Agregación: enriquece renglones, construye el árbol de grupos y resuelve totales."""` (`encino_rpt/aggregation.py:1`)
- Google-style docstrings (Spanish) on every public class and method with `Args:`, `Returns:`, `Raises:` sections — see `Report.group` (`encino_rpt/report.py:224-246`)
- Section banner comments inside longer modules: `# --- funciones / campos ---` (`encino_rpt/report.py:41`), `# --- árbol de grupos ---` (`encino_rpt/aggregation.py:116`), `# --- fase B ---` (`encino_rpt/aggregation.py:329`)
- Inline comments explain non-obvious invariants, in Spanish: `# None -> raíz (una sola partición)` (`encino_rpt/_specs.py:80`), `# children: subgrupos o detalle` (`encino_rpt/aggregation.py:245`), `# Contexto interno (no serializado)...` (`encino_rpt/models.py:123`)
- `# pragma: no cover - depende del entorno` on optional-dependency import guards (`encino_rpt/renderers/excel.py:44`, `encino_rpt/renderers/pdf.py:39`)
- Comments in source are Spanish; avoid English comments in new code.
## Function Design
- Keyword-only args after the first positional(s), marked `*`: e.g. `def set_format(self, column: str, *, kind: str = "number", decimals: int | None = None, ...)` (`encino_rpt/report.py:68-72`)
- Optional params default to `None` and are stored/checked explicitly: `columns: str | None = None`, `title: str | None = None`
- `format=None` is the one place a shadowed builtin name is used as a parameter (avoids importing `Format` in the public builder API) — `encino_rpt/report.py:127`
- Fluent builder methods return `self` typed as the class: `-> Report` (`encino_rpt/report.py:42,55,68,...`), `-> Section` (`encino_rpt/section.py:14,26,40,...`)
- `Report.run()` returns the canonical `ReportResult` (`encino_rpt/report.py:278-286`), lazily importing `build`
- Renderers return plain data: `str` (`render_html`, `to_csv`, `to_text`), `Worksheet` (`to_excel`), `bytes` (`to_pdf`) — `encino_rpt/models.py:150-214`
## Module Design
- Public API surface defined in `encino_rpt/__init__.py`: exports the models (`Chart`, `ConditionalRule`, ..., `Total`) and `Report` with an explicit `__all__`. Note `Section` is intentionally **not** exported (reachable via `Report.group()` / `Report.section()` return values).
- `encino_rpt/renderers/__init__.py` re-exports all five renderers with `__all__ = ["CsvRenderer", "ExcelRenderer", "HtmlRenderer", "PdfRenderer", "TextRenderer"]`.
- Internal modules (`_specs.py`, `aggregation.py`, `expressions.py`, `template.py`, `pivot.py`, `charts.py`, `renderers/_format.py`, `renderers/_sanitize.py`) are not exported.
- Public fluent facade: `encino_rpt/report.py` (`Report`) + `encino_rpt/section.py` (`Section`) — mutate internal spec dataclasses
- Internal specs: `encino_rpt/_specs.py` (dataclasses, `field(default_factory=list)` for mutable defaults)
- Canonical output model: `encino_rpt/models.py` (pydantic `BaseModel`, `Field(default_factory=...)` for mutable defaults, `PrivateAttr` for non-serialized context, `Group.model_rebuild()` at module end for the recursive `children: list[Detail | Group | Chart | Pivot]` reference)
- Pipeline: `encino_rpt/aggregation.py` (build tree) → `encino_rpt/charts.py` / `encino_rpt/pivot.py` (extras) → `encino_rpt/expressions.py` (safe evaluator) / `encino_rpt/template.py` (`{{token}}` rendering)
- Renderers: `encino_rpt/renderers/` — each implements a `_walk` visitor over the canonical tree (visitor pattern per `encino_rpt/renderers/__init__.py:1`)
- Optional extras imported inside methods, not at module top: `openpyxl` inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:42-44`), `reportlab` inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:30-39`), plus per-helper imports (`from openpyxl.styles import Font` inside `_full_row`, `encino_rpt/renderers/excel.py:126-127`)
- Even required internal modules are lazily imported to avoid cycles: `from .aggregation import build` inside `Report.run()` (`encino_rpt/report.py:284`), and `from .renderers.html import HtmlRenderer` inside `ReportResult.render_html` (`encino_rpt/models.py:160`)
- `aggregation.py` reaches into `Report` internals directly: `report._rows`, `report._datasets`, `report._fields`, `report._functions`, `report._groups`, `report._order` (`encino_rpt/aggregation.py:91,96,102,117-121,128,385-397`). This couples the pipeline to the builder's private state; new code should prefer adding accessor methods on `Report` if the coupling grows.
## Patterns to Follow
- Fluent builder: methods validate immediately (raise early) and return `self`
- "Truthiness coalescing" for label fallbacks: `label = t.label or t.name or t.operator` (`encino_rpt/renderers/excel.py:86`, also `html.py:58`, `csv.py:42`, `text.py:35`, `pdf.py:85`)
- Dict `or` fallback for user-supplied config: `self.styles = styles or {}`, `self.classes = classes or {}`
- Row access via `row.get(col)` with `None` fallbacks, never `row[col]`
- Module-level `_OPS`-style dispatch dicts instead of if/else chains for operator lookup
- Preserve insertion order explicitly where dicts don't: `_ordered_unique` (`encino_rpt/pivot.py:46-52`), `order` list parallel to `index` dict in `_partition` (`encino_rpt/aggregation.py:143-153`)
## Anti-Patterns
### No-op statement left in renderer
### `.__init__.py` import alignment
### Cross-module private attribute access
## Cross-Cutting Conventions
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## System Overview
```text
```
## Component Responsibilities
| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a group's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress/page_break) | `encino_rpt/section.py` |
| `FieldSpec`/`GroupSpec`/`TotalSpec`/`ChartSpec`/`PivotSpec`/`KpiSpec` | Internal builder specifications (dataclasses) — NOT part of the canonical tree | `encino_rpt/_specs.py` |
| `evaluate()` | Safe expression evaluator (AST whitelist, no `eval`, anti-DoS limits) | `encino_rpt/expressions.py` |
| `render()` | `{{token}}` template interpolation for header/footer | `encino_rpt/template.py` |
| `build()` | Orchestrates `run()`: visible columns, row enrichment, group tree construction, totals, deferred `TOTAL(...)` resolution, template rendering, KPIs → `ReportResult` | `encino_rpt/aggregation.py` |
| `build_chart()` | Derives `Chart.labels`/`series` from already-aggregated child groups or the group's own totals | `encino_rpt/charts.py` |
| `build_pivot()` | Builds a rows × columns cross-tab matrix (`Pivot`) with row/column totals | `encino_rpt/pivot.py` |
| Pydantic models | Canonical serializable tree: `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta` | `encino_rpt/models.py` |
| `HtmlRenderer` | Walks the tree → HTML `<table>` with classes, conditional styles, pivot sub-tables | `encino_rpt/renderers/html.py` |
| `ExcelRenderer` | Walks the tree → openpyxl `Worksheet` (optional dep), native charts, `=SUM(...)` formula mode, cell formatting | `encino_rpt/renderers/excel.py` |
| `CsvRenderer` | Walks the tree → flattened CSV with formula-injection sanitization | `encino_rpt/renderers/csv.py` |
| `TextRenderer` | Walks the tree → indented plain text for inspection | `encino_rpt/renderers/text.py` |
| `PdfRenderer` | Walks the tree → reportlab PDF bytes (optional dep), span-based layout | `encino_rpt/renderers/pdf.py` |
| `format_value`/`excel_number_format` | Shared value formatting per `Format` (currency, %, thousands, parens, dates) | `encino_rpt/renderers/_format.py` |
| `sanitize_csv`/`write_excel_cell` | OWASP formula-injection mitigation for CSV/Excel output | `encino_rpt/renderers/_sanitize.py` |
## Pattern Overview
- Fluent builder API returning `self` for chaining (`report.py`, `section.py`)
- Spec objects (`_specs.py`) decouple what the user declared from the canonical output
- Two-phase total resolution: base totals first, then deferred expressions using `TOTAL("seccion.nombre")` (phase B)
- Post-processing phase C: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed (`aggregation.py:277-287`)
- Pydantic v2 models with typed discriminators (`type: Literal[...]`) for polymorphic children
- Lazy imports for all optional renderer dependencies
- In-memory aggregation engine (scalability note in design doc §11: heavy aggregates delegate to SQL `ROLLUP`/`CUBE`)
## Layers
- Purpose: Declarative configuration of a report
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`
- Contains: The `Report` builder, the `Section` facade, and internal `*Spec` dataclasses
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints)
- Used by: application code (see README examples)
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`
- Location: `encino_rpt/aggregation.py` (with helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`)
- Contains: `build(report)`, partitioning, group-tree construction, total computation, template resolution, KPI computation
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`
- Used by: only `Report.run()` (`encino_rpt/report.py:278-286`)
- Purpose: Typed, JSON-serializable representation of the report result
- Location: `encino_rpt/models.py`
- Contains: 13 pydantic models (see Component Responsibilities table)
- Depends on: `pydantic>=2` only
- Used by: the engine (writes), the renderers (read), and downstream consumers (`model_dump()` / `model_validate()`)
- Purpose: Convert the canonical tree to a concrete output format
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `_format.py`, `_sanitize.py`)
- Contains: Visitor-style renderer classes + shared formatting/sanitizing helpers
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras)
- Used by: `ReportResult` convenience methods and end users
## Data Flow
### Primary Request Path (build a report)
### Secondary Flow (render to a destination)
- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:27-39`); there is no module-level mutable state.
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:381-397`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl` via pydantic `PrivateAttr` (`encino_rpt/models.py:123-126`).
- A fresh `Report` instance is required per report — `run()` does not reset the builder, so re-running `run()` re-executes the full aggregation.
## Key Abstractions
- Purpose: The serializable contract between engine and presentation; pure data
- Location: `encino_rpt/models.py:136-214`
- Pattern: pydantic `BaseModel` with typed children (`root: Group`), convenience render methods with lazy imports
- Serialization: `model_dump()` / `model_validate()` round-trip verified in `tests/test_report.py:235-243`
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it
- Location: `encino_rpt/_specs.py:77-97`, `encino_rpt/section.py`
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`report.py:261-276`)
- Purpose: Computed fields, conditional totals, and ordering expressions
- Location: `encino_rpt/expressions.py:54-60`
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:63-109`); no `eval`
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:45-47`)
- Purpose: Uniform tree walking across output formats
- Location: `encino_rpt/renderers/` — each renderer implements `render(result)` and a recursive `_walk`/`_collect(node, ...)`
- Pattern: dispatch by `isinstance` over `Group` / `Detail` / `Chart` / `Pivot`; KPIs and column header handled before walking
- Extension: add a new renderer class implementing the same `render(result)` contract; register it in `encino_rpt/renderers/__init__.py`
- Purpose: Separate what the user declared (`FieldSpec`, `GroupSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec` — `_specs.py`) from the produced output (`Total`, `Group`, `Chart`, `Pivot`, `Kpi`, `Detail` — `models.py`)
- Pattern: engine maps specs → models during `build()`; specs never appear in the output tree
## Entry Points
- Location: `encino_rpt/__init__.py`
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, ...`
- Responsibilities: re-export the builder and the canonical model types; `__all__` lists 14 public names (`__init__.py:20-34`)
- Location: `encino_rpt/report.py:278-286`
- Triggers: user call after declaring the report
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`
- Location: `encino_rpt/models.py:150-214` (`render_html`, `to_csv`, `to_text`, `to_excel`, `to_pdf`)
- Triggers: end-user call on the result
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree
## Architectural Constraints
- **Threading:** Single-threaded, in-memory aggregation. No threads, no async, no shared state outside the `Report` instance. Engine helpers in `aggregation.py` are module-level functions with private `_`-prefixed names (importing them is discouraged).
- **Global state:** None at module level. All mutable state is per-`Report` instance or local to `build()`.
- **Circular imports:** Avoided. `report.py` imports `aggregation.py` lazily inside `run()` (`report.py:284`); `models.py` imports renderers lazily inside convenience methods (`models.py:160-213`). `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`expressions.py`). `ast.parse` node/depth counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`renderers/excel.py:41-45`); `reportlab` only inside `PdfRenderer.render` (`renderers/pdf.py:29-40`). Both raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"`; CI matrix runs 3.10–3.13 (`.github/workflows/ci.yml:12-13`). Code uses `from __future__ import annotations` throughout.
- **Pydantic forward references:** `Group.children` is a recursive union, resolved with `Group.model_rebuild()` at the bottom of `encino_rpt/models.py:217`.
## Anti-Patterns
### Tight coupling between `aggregation.py` and private `Report` attributes
### Charts/pivots appended after phase-C ordering
### Duplicated visitor dispatch and operator tables per renderer
## Error Handling
- Builder validation: `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:247-248`); `section()` raises `KeyError` for undeclared cuts (`report.py:274-275`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:130-131`).
- Expression errors: `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`expressions.py:50-52,58-59,69,73,77,81,87,93,98,101,104,106,109`).
- Template errors: `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params (`template.py:23-26`).
- Aggregate errors: `ValueError` for unknown operators (`aggregation.py:45`).
- Optional dependency errors: `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:44-45`, `renderers/pdf.py:39-40`) — covered by `pytest.importorskip` in tests.
- Aggregation never catches exceptions: a failing expression propagates up through `run()` to the caller.
## Cross-Cutting Concerns
- Expression sandbox: AST whitelist, no `eval` (`encino_rpt/expressions.py`)
- Formula injection protection: CSV/Excel output sanitized (`encino_rpt/renderers/_sanitize.py`, tested in `tests/test_security.py:9-28`)
- HTML escaping of all emitted text and style-property whitelist regex `_SAFE_PROP` (`renderers/html.py:20,104-105,108-124`, tested in `tests/test_security.py:45-54`)
- Anti-DoS limits on expression size/depth/exponent (`expressions.py:45-47`, tested in `tests/test_security.py:31-42`)
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



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
