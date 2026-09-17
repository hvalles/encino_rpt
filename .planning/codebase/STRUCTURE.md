# Codebase Structure

**Analysis Date:** 2026-09-17

## Directory Layout

```
report/                          # repo root (encino-rpt)
├── encino_rpt/                  # Library package (pure Python, pydantic only)
│   ├── __init__.py              # Public re-exports (14 names)
│   ├── report.py                # Report fluent builder
│   ├── section.py               # Section facade (mutates GroupSpec)
│   ├── _specs.py                # Internal *Spec dataclasses (not in output tree)
│   ├── aggregation.py           # Engine: enrich → group tree → totals → ReportResult
│   ├── expressions.py           # Safe AST-whitelist expression evaluator
│   ├── template.py              # {{token}} template interpolation
│   ├── charts.py                # Chart labels/series derivation
│   ├── pivot.py                 # Cross-tab Pivot builder
│   ├── models.py                # Pydantic v2 canonical data model
│   └── renderers/               # Visitor-style output renderers
│       ├── __init__.py          # Renderer re-exports
│       ├── _walk.py             # Shared iterative tree traversal (walk generator)
│       ├── _format.py           # Value/number formatting per Format
│       ├── _sanitize.py         # OWASP formula-injection mitigation
│       ├── html.py              # HTML table renderer
│       ├── excel.py             # openpyxl renderer (optional extra)
│       ├── csv.py               # CSV renderer
│       ├── text.py              # Plain-text renderer
│       ├── pdf.py               # reportlab renderer (optional extra)
│       └── json.py              # JSON renderer (schema_version)
├── tests/                       # pytest suite (co-located by area)
│   ├── test_report.py           # Builder + engine round-trip
│   ├── test_report_renderers.py # Renderer output assertions
│   ├── test_security.py         # Expression sanitization + formula injection
│   └── test_perf_smoke.py       # 50k-row wall-clock smoke test
├── docs/                        # mkdocs source (Spanish)
│   ├── index.md / getting-started.md / guide.md / api.md / security.md
│   └── design/                  # 10-report.md design notes
├── .github/workflows/           # ci.yml, docs.yml, publish.yml
├── .planning/                   # GSD planning artifacts (codebase/, phases/, ROADMAP.md, STATE.md…)
├── prompts/                     # Internal notes (gitignored, not distributed)
├── dist/                        # Build artifacts (gitignored; version 0.2.0)
├── site/                        # Built mkdocs site (gitignored)
├── .venv/                       # Local virtualenv (gitignored)
├── .mypy_cache/ .pytest_cache/ .ruff_cache/   # Tool caches (gitignored)
├── pyproject.toml               # hatchling build + project metadata + tool config
├── uv.lock                      # Pinned dependency lockfile (uv)
├── mkdocs.yml                   # Docs site config (material theme, es)
├── README.md                    # Package overview + usage examples
├── LICENSE                      # MIT
└── AGENTS.md                    # GSD project context (generated)
```

## Directory Purposes

**`encino_rpt/`:**
- Purpose: The entire library. Pure Python, single runtime dependency (`pydantic>=2`).
- Contains: Builder (`report.py`, `section.py`), internal specs (`_specs.py`), engine (`aggregation.py`), helpers (`expressions.py`, `template.py`, `charts.py`, `pivot.py`), canonical model (`models.py`), and the `renderers/` subpackage.
- Key files: `encino_rpt/report.py`, `encino_rpt/aggregation.py`, `encino_rpt/models.py`.

**`encino_rpt/renderers/`:**
- Purpose: Convert the canonical `ReportResult` tree to concrete output formats (HTML, Excel, CSV, text, PDF, JSON).
- Contains: Six `*Renderer` classes + three shared helpers (`_walk.py`, `_format.py`, `_sanitize.py`).
- Key files: `encino_rpt/renderers/_walk.py` (the single traversal), `encino_rpt/renderers/excel.py` (largest, optional `openpyxl`).

**`tests/`:**
- Purpose: pytest suite; mirrors the library by area (engine, renderers, security, performance).
- Contains: `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_perf_smoke.py`.
- Key files: `tests/test_report.py` (555 lines), `tests/test_report_renderers.py` (357 lines).

**`docs/`:**
- Purpose: mkdocs source documentation (Spanish), published to GitHub Pages.
- Contains: `index.md`, `getting-started.md`, `guide.md`, `api.md`, `security.md`, plus `docs/design/10-report.md` (design notes).
- Key files: `docs/api.md` (API reference via mkdocstrings), `docs/design/10-report.md`.

**`.github/workflows/`:**
- Purpose: CI (`ci.yml` — test + lint + mypy), docs deploy (`docs.yml`), PyPI publish (`publish.yml`).
- Key files: `.github/workflows/ci.yml`, `.github/workflows/publish.yml`.

**`.planning/`:**
- Purpose: GSD planning state (roadmap, requirements, strategy, phase plans, codebase map).
- Contains: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `STRATEGY.md`, `config.json`, `codebase/`, `phases/`.

## Key File Locations

**Entry Points:**
- `encino_rpt/__init__.py`: Public API surface — re-exports `Report` + 13 model types (`__all__` at lines 20–34).
- `encino_rpt/report.py:361-369`: `Report.run()` — the single engine invocation point.
- `encino_rpt/models.py:150-229`: `ReportResult.render_html`/`to_csv`/`to_text`/`to_excel`/`to_json`/`to_pdf` — renderer entry points.

**Configuration:**
- `pyproject.toml`: hatchling build config, project metadata, optional extras (`excel`/`pdf`), dev/docs dependency groups, pytest/mypy/ruff/coverage tool config.
- `mkdocs.yml`: docs site config (material theme, `language: es`, mkdocstrings Google-style, 5-page nav).
- `.github/workflows/ci.yml`, `docs.yml`, `publish.yml`: CI/docs/publish pipelines.

**Core Logic:**
- `encino_rpt/aggregation.py`: `build()` orchestrates the whole engine (566 lines).
- `encino_rpt/expressions.py`: `evaluate()` safe expression evaluator.
- `encino_rpt/models.py`: canonical pydantic data model.

**Testing:**
- `tests/test_report.py`: engine + model round-trip tests.
- `tests/test_report_renderers.py`: renderer output tests.
- `tests/test_security.py`: security tests (expression whitelist, formula injection).
- `tests/test_perf_smoke.py`: performance smoke test (50k rows, 10s wall-clock bound).

## Naming Conventions

**Files:**
- `snake_case.py` for all modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `expressions.py`, `template.py`, `charts.py`, `models.py`.
- Leading-underscore for internal modules: `_specs.py`, `renderers/_walk.py`, `renderers/_format.py`, `renderers/_sanitize.py`.
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_perf_smoke.py`.

**Directories:**
- Single package `encino_rpt/` with a `renderers/` subpackage for output format code; helpers live alongside the modules they serve (engine helpers are top-level modules, renderer helpers are underscore-prefixed in `renderers/`).

**Symbols:**
- Classes `PascalCase`: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Total`, `Chart`, `Pivot`, `Kpi`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`.
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `PdfRenderer`, `TextRenderer`.
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (`encino_rpt/_specs.py`).
- Functions/variables `snake_case`; private helpers prefixed `_`; module-level constants `UPPER_SNAKE` (e.g. `_MAX_NODES`, `SCHEMA_VERSION = "1.0"`).

## Where to Add New Code

**New Feature (engine behavior):**
- Primary code: `encino_rpt/aggregation.py` (or a new helper module imported by it, following the `charts.py`/`pivot.py` pattern).
- Builder surface: add the fluent method to `encino_rpt/report.py` (or `encino_rpt/section.py` for group-scoped presentation), backing it with a field on the relevant `*Spec` in `encino_rpt/_specs.py`.
- Canonical output: if the feature produces new tree data, add the model to `encino_rpt/models.py` and extend the `Group.children` union (`models.py:121`).

**New Renderer / output format:**
- Implementation: new `encino_rpt/renderers/<name>.py` with a `*Renderer` class exposing `render(result)` that consumes `walk()` from `encino_rpt/renderers/_walk.py`.
- Registration: import it in `encino_rpt/renderers/__init__.py` and add it to `__all__`; optionally add a `ReportResult` convenience method in `encino_rpt/models.py` (lazy import, matching the existing pattern).
- Shared helpers: reuse `format_value`/`excel_number_format` (`_format.py`) and sanitization (`_sanitize.py`).

**New Model Type:**
- Implementation: `encino_rpt/models.py` (pydantic v2, `type: Literal[...]` discriminator); if recursive, call `model_rebuild()` at the bottom.

**Utilities:**
- Shared renderer helpers: `encino_rpt/renderers/_<name>.py` (underscore prefix).
- Engine helpers: top-level module in `encino_rpt/` (e.g. `charts.py`, `pivot.py`).

**Tests:**
- Add to `tests/test_<area>.py`, or create `tests/test_<new_area>.py` following the existing naming.

## Special Directories

**`site/`:**
- Purpose: Built mkdocs HTML output (published to GitHub Pages).
- Generated: Yes (`mkdocs build`).
- Committed: No (`.gitignore:15`).

**`dist/`:**
- Purpose: Built wheel/sdist artifacts (`encino_rpt-0.2.0-py3-none-any.whl`, `encino_rpt-0.2.0.tar.gz`).
- Generated: Yes (`uv build`).
- Committed: No (`.gitignore:12`; also self-ignored via `dist/.gitignore`).

**`prompts/`:**
- Purpose: Internal dev notes (`24.md`, `25.md`, `analisys-10.md`).
- Generated: No.
- Committed: No (`.gitignore:28`).

**`.venv/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`:**
- Purpose: Local environment and tool caches.
- Generated: Yes.
- Committed: No (`.gitignore:1-20`).

---

*Structure analysis: 2026-09-17*
