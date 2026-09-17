# Codebase Structure

**Analysis Date:** 2026-09-17

## Directory Layout

```
report/                              # repo root (encino-rpt)
├── encino_rpt/                      # Python package (the library itself)
│   ├── __init__.py                  # public API: re-exports models + Report
│   ├── report.py                    # fluent Report builder
│   ├── section.py                   # fluent Section facade (mutates a GroupSpec)
│   ├── _specs.py                    # internal builder dataclasses (FieldSpec, GroupSpec, ...)
│   ├── aggregation.py               # in-memory aggregation engine (build())
│   ├── expressions.py               # safe AST expression evaluator (no eval)
│   ├── template.py                  # {{token}} template interpolation
│   ├── charts.py                    # Chart derivation from aggregated data
│   ├── pivot.py                     # cross-tab (rows×columns) Pivot construction
│   ├── models.py                    # canonical pydantic tree (ReportResult, Group, ...)
│   └── renderers/                   # visitor renderers + shared helpers
│       ├── __init__.py              # re-exports all 6 renderers
│       ├── _walk.py                 # shared iterative tree traversal (walk())
│       ├── _format.py               # format_value / excel_number_format
│       ├── _sanitize.py             # OWASP formula-injection mitigation
│       ├── html.py                  # HtmlRenderer
│       ├── excel.py                 # ExcelRenderer (openpyxl, optional)
│       ├── csv.py                   # CsvRenderer
│       ├── text.py                  # TextRenderer
│       ├── pdf.py                   # PdfRenderer (reportlab, optional)
│       └── json.py                  # JsonRenderer (schema-versioned)
├── tests/                           # pytest suite
│   ├── test_report.py               # builder/engine/round-trip
│   ├── test_report_renderers.py     # all renderers
│   └── test_security.py             # sandbox + injection + escaping
├── docs/                            # mkdocs source (Markdown)
│   ├── index.md · api.md · guide.md · getting-started.md · security.md
│   └── design/10-report.md          # design doc
├── .github/workflows/               # ci.yml · docs.yml · publish.yml
├── .planning/                       # GSD planning artifacts (project/roadmap/state/phases)
│   ├── codebase/                    # this codebase map (STACK/ARCH/CONVENTIONS/...)
│   └── phases/                      # phase plans & summaries
├── site/                            # built mkdocs output (generated, committed)
├── prompts/                         # ad-hoc prompt notes (24.md, analisys-10.md)
├── dist/                            # built wheels/sdists (generated, gitignored)
├── pyproject.toml                   # project metadata, deps, pytest config
├── mkdocs.yml                       # docs site config
├── uv.lock                          # pinned dependency lockfile (uv)
├── README.md · LICENSE · AGENTS.md · .gitignore
└── .venv/ · .ruff_cache/ · .pytest_cache/ · __pycache__/   # local/generated (gitignored)
```

## Directory Purposes

**encino_rpt/:**
- Purpose: The entire library — a pure-Python financial report engine over `list[dict]`.
- Contains: builder (`report.py`, `section.py`), specs (`_specs.py`), engine (`aggregation.py` + `expressions.py`/`template.py`/`charts.py`/`pivot.py`), canonical model (`models.py`), and renderers.
- Key files: `encino_rpt/__init__.py`, `encino_rpt/report.py`, `encino_rpt/aggregation.py`, `encino_rpt/models.py`.

**encino_rpt/renderers/:**
- Purpose: Convert the canonical tree to concrete output formats.
- Contains: six renderers plus three internal helpers (`_walk.py`, `_format.py`, `_sanitize.py`).
- Key files: `encino_rpt/renderers/_walk.py` (shared traversal), `encino_rpt/renderers/__init__.py`.

**tests/:**
- Purpose: pytest suite covering builder/engine, renderers, and security.
- Contains: `test_report.py`, `test_report_renderers.py`, `test_security.py`.
- Key files: `tests/test_report.py` (437 lines — largest, engine + round-trip).

**docs/:**
- Purpose: mkdocs source for the public documentation site.
- Contains: user guide, API reference, getting-started, security notes, and the design doc `docs/design/10-report.md`.
- Key files: `docs/design/10-report.md` (design source of truth).

**.planning/:**
- Purpose: GSD workflow artifacts (strategy, roadmap, state, phase plans).
- Contains: `PROJECT.md`, `STRATEGY.md`, `ROADMAP.md`, `STATE.md`, `REQUIREMENTS.md`, `config.json`, and `phases/` + `codebase/`.
- Key files: `.planning/codebase/` (this map), `.planning/STATE.md`.

**.github/workflows/:**
- Purpose: CI/CD pipeline definitions.
- Contains: `ci.yml` (lint + test matrix 3.10–3.13), `docs.yml` (mkdocs build/deploy), `publish.yml` (PyPI/TestPyPI release).
- Key files: `.github/workflows/ci.yml`.

**site/ and dist/:**
- Purpose: `site/` is generated mkdocs HTML (committed for GitHub Pages); `dist/` holds built wheel/sdist artifacts.
- Generated: Yes (both). `site/` is committed; `dist/` is gitignored.

## Key File Locations

**Entry Points:**
- `encino_rpt/__init__.py`: public package API (`__all__` with 14 names).
- `encino_rpt/report.py:280-288`: `Report.run()` — the engine trigger.
- `encino_rpt/models.py:150-227`: `ReportResult` convenience render methods.

**Configuration:**
- `pyproject.toml`: project metadata, dependencies, optional extras (`excel`/`pdf`), dev/docs groups, pytest options.
- `mkdocs.yml`: docs site config (material theme, mkdocstrings).
- `.github/workflows/*.yml`: CI/docs/publish pipelines.

**Core Logic:**
- `encino_rpt/aggregation.py`: `build()` and all engine helpers.
- `encino_rpt/expressions.py`: `evaluate()` sandbox.
- `encino_rpt/models.py`: canonical pydantic tree.

**Rendering:**
- `encino_rpt/renderers/_walk.py`: shared traversal.
- `encino_rpt/renderers/{html,excel,csv,text,pdf,json}.py`: the six renderers.

**Testing:**
- `tests/test_report.py`, `tests/test_report_renderers.py`, `tests/test_security.py`.

## Naming Conventions

**Files:**
- `snake_case.py` for modules: `report.py`, `section.py`, `aggregation.py`, `pivot.py`, `charts.py`.
- Leading underscore for internal modules/helpers: `_specs.py`, `renderers/_format.py`, `renderers/_sanitize.py`, `renderers/_walk.py`.
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`.

**Directories:**
- One package (`encino_rpt`) plus `renderers/` subpackage; docs at `docs/`; tests at `tests/`.

**Classes:**
- PascalCase models: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`.
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `PdfRenderer`, `TextRenderer`, `JsonRenderer`.
- Spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec`.
- Private engine class `_PathNode` (trie node, `aggregation.py:214`).

**Functions:**
- `snake_case` public: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`, `build`.
- Private module helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_esc`, `_walk`, `_partition`, `_segs`.
- Dispatch dicts `_OPS`/`_COLOR_OPS`/`_BINOPS`/`_UNARY`/`_CMP`/`_FUNCTIONS`.

## Where to Add New Code

**New Feature (a new cut type / builder method):**
- Builder method: `encino_rpt/report.py` (mutate `Report` state and return `self`).
- Spec dataclass field (if needed): `encino_rpt/_specs.py`.
- Engine handling: `encino_rpt/aggregation.py`.
- Canonical model (if new output node): `encino_rpt/models.py`.
- Tests: `tests/test_report.py`.

**New Renderer (a new output format):**
- Implementation: `encino_rpt/renderers/<name>.py` — implement `render(result)` consuming `walk()` from `encino_rpt/renderers/_walk.py`.
- Registration: add the import + name to `encino_rpt/renderers/__init__.py` (`__all__`).
- Optional convenience method: `encino_rpt/models.py` (lazy import + delegate).
- Tests: `tests/test_report_renderers.py`.

**Utilities (shared across renderers):**
- Formatting helpers: `encino_rpt/renderers/_format.py`.
- Security/sanitization helpers: `encino_rpt/renderers/_sanitize.py`.

**Documentation:**
- Markdown pages: `docs/` (add to `mkdocs.yml` `nav`).

## Special Directories

**site/:**
- Purpose: Built mkdocs HTML for GitHub Pages.
- Generated: Yes (via `mkdocs build` in `.github/workflows/docs.yml`).
- Committed: Yes.

**dist/:**
- Purpose: Built wheel (`encino_rpt-0.2.0-py3-none-any.whl`) and sdist artifacts.
- Generated: Yes (via `uv build` in `.github/workflows/publish.yml`).
- Committed: No (gitignored).

**.venv/, .ruff_cache/, .pytest_cache/, __pycache__/:**
- Purpose: Local dev environment and caches.
- Generated: Yes.
- Committed: No (gitignored).

**.planning/:**
- Purpose: GSD planning/execution artifacts (strategy, roadmap, state, phase plans, codebase map).
- Generated: By GSD commands.
- Committed: Yes.

---

*Structure analysis: 2026-09-17*
