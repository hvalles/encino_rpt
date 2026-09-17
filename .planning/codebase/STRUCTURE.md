# Codebase Structure

**Analysis Date:** 2026-09-17

## Directory Layout

```
report/                            # repo root (encino-rpt)
├── encino_rpt/                    # the library package (published as `encino-rpt`)
│   ├── __init__.py                # public API re-exports (15 names)
│   ├── report.py                  # fluent `Report` builder + read()/register_reader()
│   ├── section.py                 # `Section` facade (mutates a GroupSpec)
│   ├── readers.py                 # multi-format input readers (Reader protocol + registry)
│   ├── aggregation.py             # aggregation engine (enrich/group/totals/templates/KPIs)
│   ├── expressions.py             # safe AST expression evaluator (no eval)
│   ├── template.py                # `{{token}}` interpolation
│   ├── charts.py                  # Chart label/series derivation
│   ├── pivot.py                   # Pivot cross-tab builder
│   ├── models.py                  # pydantic canonical tree (13 models)
│   ├── _specs.py                  # internal builder dataclasses (FieldSpec/GroupSpec/...)
│   └── renderers/                 # output renderers (visitor pattern)
│       ├── __init__.py            # exports the 7 renderer classes
│       ├── _walk.py               # shared iterative traversal (single source of truth)
│       ├── _format.py             # format_value / excel_number_format
│       ├── _sanitize.py           # OWASP formula-injection mitigation
│       ├── html.py                # HtmlRenderer
│       ├── excel.py               # ExcelRenderer (openpyxl, optional)
│       ├── csv.py                 # CsvRenderer
│       ├── text.py                # TextRenderer
│       ├── pdf.py                 # PdfRenderer (reportlab, optional)
│       ├── json.py                # JsonRenderer (schema_version)
│       └── markdown.py            # MarkdownRenderer (GFM tables)
├── tests/                         # pytest suite (5 files, ~1480 lines)
│   ├── test_report.py             # builder + model round-trip
│   ├── test_report_renderers.py   # renderer output
│   ├── test_readers.py            # multi-format readers
│   ├── test_security.py           # expression + formula-injection safety
│   └── test_perf_smoke.py         # performance smoke tests
├── docs/                          # mkdocs source (Spanish), includes design/ subdir
├── .github/workflows/             # ci.yml, docs.yml, publish.yml
├── dist/                          # built wheel/sdist (gitignored, version 0.2.0)
├── site/                          # built mkdocs site (gitignored)
├── .planning/                     # GSD planning artifacts (codebase/ lives here)
├── pyproject.toml                 # hatchling build + tool configs (pytest/mypy/ruff/coverage)
├── mkdocs.yml                     # docs config
├── uv.lock                        # uv lockfile (all deps pinned)
├── AGENTS.md                      # project context (GSD-generated)
├── README.md
└── LICENSE
```

## Directory Purposes

**`encino_rpt/` (package root):**
- Purpose: The entire public library. Pure Python, no server, no compiled extensions.
- Contains: Builder, engine, models, readers, and renderers.
- Key files: `report.py`, `aggregation.py`, `models.py`, `readers.py`, `__init__.py`.

**`encino_rpt/renderers/`:**
- Purpose: Convert the canonical tree to concrete output formats (visitor pattern).
- Contains: 7 renderer classes + 3 shared helpers (`_walk.py`, `_format.py`, `_sanitize.py`).
- Key files: `_walk.py` (shared traversal), `html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `markdown.py`.

**`tests/`:**
- Purpose: pytest suite covering builder/model round-trip, renderers, readers, security, and performance.
- Contains: `test_*.py` modules, one per area.
- Key files: `test_report.py`, `test_report_renderers.py`, `test_readers.py`, `test_security.py`.

**`docs/`:**
- Purpose: mkdocs source (Spanish) with `getting-started.md`, `guide.md`, `api.md`, `security.md`, and a `design/` subdirectory.
- Contains: Markdown documentation and mkdocstrings references.
- Key files: `index.md`, `api.md`.

**`.github/workflows/`:**
- Purpose: CI (`ci.yml`), docs deployment (`docs.yml`), and package publishing (`publish.yml`).
- Contains: GitHub Actions workflow YAML.
- Key files: `ci.yml`.

**`.planning/`:**
- Purpose: GSD planning artifacts (roadmap, state, strategy, and `codebase/` maps).
- Contains: Markdown planning docs; `codebase/` holds the architecture/stack/convention maps.
- Key files: `codebase/ARCHITECTURE.md`, `codebase/STRUCTURE.md`.

## Key File Locations

**Entry Points:**
- `encino_rpt/__init__.py`: public API — re-exports 15 names (`Report`, `ReportResult`, all model types, `Reader`).
- `encino_rpt/report.py`: `Report.run()` (materialize), `Report.read()` / `Report.register_reader()` (input).
- `encino_rpt/readers.py`: `read()` function (dispatch by format/extension).
- `encino_rpt/models.py`: `ReportResult.to_*`/`render_*`/`iter_*` convenience methods.

**Configuration:**
- `pyproject.toml`: hatchling build config, dependency groups, and `[tool.pytest.ini_options]`, `[tool.mypy]`, `[tool.ruff]`, `[tool.coverage]` sections.
- `mkdocs.yml`: docs config.
- `.github/workflows/ci.yml`: test (matrix 3.10–3.13) and quality (mypy/ruff/coverage) jobs.

**Core Logic:**
- `encino_rpt/aggregation.py`: the engine — `build()` orchestrates enrichment, grouping, totals, templates, KPIs.
- `encino_rpt/expressions.py`: `evaluate()` safe expression evaluator.
- `encino_rpt/models.py`: canonical pydantic tree.

**Testing:**
- `tests/test_report.py`, `tests/test_report_renderers.py`, `tests/test_readers.py`, `tests/test_security.py`, `tests/test_perf_smoke.py`.

**Docs:**
- `docs/guide.md`, `docs/api.md`, `docs/security.md`, `docs/design/`.

## Naming Conventions

**Files:**
- `snake_case.py` modules in the package root: `report.py`, `aggregation.py`, `expressions.py`, `readers.py`.
- Leading underscore for internal/helper modules: `_specs.py`, `renderers/_walk.py`, `renderers/_format.py`, `renderers/_sanitize.py`.
- Tests: `tests/test_<area>.py`.

**Directories:**
- `renderers/` for output; `docs/` for mkdocs source; `.github/workflows/` for CI.

**Classes:**
- `PascalCase`: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`, `Reader`.
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `MarkdownRenderer`, `PdfRenderer`, `TextRenderer`.
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (`encino_rpt/_specs.py`).
- Reader classes suffixed `Reader`: `JsonReader`, `JsonLinesReader`, `TuplesReader`, `ExcelReader`; base helper `_DelimitedReader` (internal, `_`-prefixed).

**Functions:**
- `snake_case`: `add_field`, `add_function`, `add_aggregate`, `build_chart`, `build_pivot`, `evaluate`, `render`, `build`, `read`, `register_reader`, `get_reader`, `format_value`, `sanitize_csv`, `walk`.
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_enrich`, `_partition`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_coerce`, `_read_text`, `_resolve_format`.

## Where to Add New Code

**New Feature (builder capability):**
- Primary code: add the fluent method to `encino_rpt/report.py`; if it needs spec state, add fields to the relevant dataclass in `encino_rpt/_specs.py`; add the aggregation logic in `encino_rpt/aggregation.py` (and register any validation in `_validate`).
- Tests: `tests/test_report.py`.

**New Output Format (renderer):**
- Implementation: create `encino_rpt/renderers/<name>.py` with a `<Name>Renderer` class that consumes `walk()` from `encino_rpt/renderers/_walk.py` and implements `render(result)` + `iter_*`/`write(result, file)`.
- Register: add the import and name to `encino_rpt/renderers/__init__.py` (`__all__`).
- Expose: add a `to_<name>()`/`iter_<name>()` convenience method to `ReportResult` in `encino_rpt/models.py`.
- Tests: `tests/test_report_renderers.py`.

**New Input Format (reader):**
- Implementation: add a reader class in `encino_rpt/readers.py` (or a custom object with a `read(source, **opts) -> list[dict]` method), then `register_reader("name", reader)` at the bottom of `readers.py`. Add its extension to `_FORMAT_BY_EXT` (`readers.py:318-325`) if it should resolve by extension.
- Registration: use `Report.register_reader(name, reader)` (`encino_rpt/report.py:80-90`) for user-level custom readers.
- Tests: `tests/test_readers.py`.

**New Canonical Model Type:**
- Implementation: add the pydantic model to `encino_rpt/models.py`; if it is a child node type, add it to the `Group.children` union and re-run `Group.model_rebuild()`.
- Tests: `tests/test_report.py`.

**Utilities:**
- Shared helpers live in the package root (`expressions.py`, `template.py`, `charts.py`, `pivot.py`) or `encino_rpt/renderers/_*.py` if renderer-specific.
- Private/internal code goes in `_`-prefixed modules (`_specs.py`, `renderers/_walk.py`, `renderers/_format.py`, `renderers/_sanitize.py`).

## Special Directories

**`dist/`:**
- Purpose: Built wheel and sdist (`encino_rpt-0.2.0-*`).
- Generated: Yes (via `uv build` in `.github/workflows/publish.yml`).
- Committed: No (gitignored).

**`site/`:**
- Purpose: Built mkdocs site output.
- Generated: Yes (via `mkdocs build`).
- Committed: No (gitignored).

**`.venv/`:**
- Purpose: Local dev virtualenv (Windows; created by `uv`).
- Generated: Yes.
- Committed: No (gitignored).

**`.planning/`:**
- Purpose: GSD planning artifacts, including this `codebase/` map.
- Generated: Yes (by GSD commands).
- Committed: Yes.

**`.github/workflows/`:**
- Purpose: CI, docs deploy, and publish pipelines.
- Generated: No (hand-written).
- Committed: Yes.

---

*Structure analysis: 2026-09-17*
