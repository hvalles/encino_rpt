# Codebase Structure

**Analysis Date:** 2026-09-16

## Directory Layout

```
report/
├── encino_rpt/             # Main package (the library)
│   ├── __init__.py         # Public API re-exports
│   ├── _specs.py           # Internal builder spec dataclasses
│   ├── report.py           # Report fluent builder
│   ├── section.py          # Section facade (mutates GroupSpec)
│   ├── expressions.py      # Safe expression evaluator (AST whitelist)
│   ├── template.py         # {{token}} template interpolation
│   ├── aggregation.py      # Engine: build() orchestration
│   ├── charts.py           # Chart node derivation
│   ├── pivot.py            # Pivot (cross-tab) construction
│   ├── models.py           # Canonical pydantic data model
│   └── renderers/          # Visitor-pattern output renderers
│       ├── __init__.py     # Renderer exports
│       ├── html.py         # HTML table renderer
│       ├── excel.py        # openpyxl renderer (optional dep)
│       ├── csv.py          # Flattened CSV renderer
│       ├── text.py         # Plain-text renderer
│       ├── pdf.py          # reportlab renderer (optional dep)
│       ├── _format.py      # Shared value formatting helpers
│       └── _sanitize.py    # Formula-injection mitigation
├── tests/                  # pytest suite
│   ├── test_report.py      # Builder/aggregation/expressions tests
│   ├── test_report_renderers.py  # Format + renderer tests
│   └── test_security.py    # Security mitigation tests
├── docs/                   # mkdocs documentation source
│   ├── index.md            # Home
│   ├── getting-started.md  # 5-step quick start
│   ├── guide.md            # Usage guide
│   ├── api.md              # API reference (mkdocstrings)
│   ├── security.md         # Security mitigations
│   └── design/
│       └── 10-report.md    # Original design document (authoritative)
├── .github/workflows/      # GitHub Actions CI/CD
│   ├── ci.yml              # Test + lint matrix (3.10–3.13)
│   ├── publish.yml         # PyPI/TestPyPI publishing
│   └── docs.yml            # mkdocs → GitHub Pages
├── prompts/                # Internal design notes (gitignored)
├── site/                   # Generated mkdocs output (gitignored)
├── dist/                   # Built wheel/sdist artifacts (gitignored)
├── pyproject.toml          # Package metadata, deps, pytest/ruff config
├── uv.lock                 # uv lockfile
├── mkdocs.yml              # Docs site config
├── README.md               # Project readme (Spanish)
├── LICENSE                 # MIT
└── .gitignore
```

## Directory Purposes

**`encino_rpt/` (root package):**
- Purpose: The library itself — builder, engine, model, and renderers
- Contains: 11 Python modules + `renderers/` subpackage
- Key files: `__init__.py` (public API), `report.py` (builder entry point), `aggregation.py` (engine core), `models.py` (canonical tree)

**`encino_rpt/renderers/`:**
- Purpose: Output-format conversion (visitor pattern)
- Contains: One renderer class per format + two shared private helpers
- Key files: `html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `_format.py`, `_sanitize.py`

**`tests/`:**
- Purpose: Full pytest suite
- Contains: 3 test modules covering expressions, builder, aggregation, renderers, and security
- Key files: `test_report.py` (largest — core behavior), `test_security.py` (P1–P4 mitigations)

**`docs/`:**
- Purpose: mkdocs documentation source (Spanish)
- Contains: User docs plus the original design document
- Key file: `docs/design/10-report.md` — exhaustive design spec; the implementation follows it closely (notable drift: design proposed `renderers.py`; implementation split into `renderers/` package)

**`.github/workflows/`:**
- Purpose: CI/CD
- Contains: 3 workflows
- Key file: `ci.yml` — runs `uv run pytest` and `uv run ruff check` on Python 3.10–3.13

**`prompts/`:**
- Purpose: Internal analysis notes that drove the design (gitignored via `.gitignore:28`)
- Contains: `24.md`, `analisys-10.md`
- Note: Not part of the shipped package (`prompts/` in `.gitignore`)

**`site/` and `dist/`:**
- Purpose: Generated artifacts — mkdocs build output and `uv build` wheel/sdist
- Generated: Yes (both gitignored — `.gitignore:11,15`)

## Key File Locations

**Entry Points:**
- `encino_rpt/__init__.py`: Public API — exports `Report`, `ReportResult`, and 12 model types (`__init__.py:20-34`)
- `encino_rpt/report.py:278`: `Report.run()` — engine entry point
- `encino_rpt/models.py:150-214`: `ReportResult.render_html` / `to_csv` / `to_text` / `to_excel` / `to_pdf` — renderer entry points

**Configuration:**
- `pyproject.toml`: Package metadata, build backend (hatchling), dependencies, pytest `testpaths`/`pythonpath`, dev/docs dependency groups
- `mkdocs.yml`: Docs site config (mkdocs-material, mkdocstrings)
- `uv.lock`: Locked dependency resolution (uv)

**Core Logic:**
- `encino_rpt/report.py`: Fluent builder (`Report` class, 286 lines)
- `encino_rpt/aggregation.py`: Engine — `build()` plus all grouping/total/template logic (406 lines, the largest module)
- `encino_rpt/models.py`: Canonical pydantic model (217 lines)
- `encino_rpt/expressions.py`: Safe expression evaluator (109 lines)
- `encino_rpt/section.py`: Per-group presentation facade (175 lines)

**Testing:**
- `tests/test_report.py`: Builder + aggregation behavior (269 lines)
- `tests/test_report_renderers.py`: `format_value` + renderer output (120 lines)
- `tests/test_security.py`: Security mitigation tests (63 lines)

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` — `report.py`, `section.py`, `aggregation.py`, `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`
- Private/internal modules: `_`-prefixed — `_specs.py` (builder specs), `_format.py` and `_sanitize.py` (renderer internals)
- Tests: `test_<suffix>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`

**Directories:**
- Subpackages: single-word lowercase — `renderers/`, `tests/`, `docs/`
- Generated dirs excluded from source: `site/`, `dist/`, `.venv/`

**Classes:**
- `PascalCase` — `Report`, `Section`, `ReportResult`, `ReportMeta`, `HtmlRenderer`, `ExcelRenderer`, `CsvRenderer`, `TextRenderer`, `PdfRenderer`, `ExpressionError`
- Spec dataclasses: `*Spec` suffix — `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (`encino_rpt/_specs.py`)
- Canonical nodes: singular model names — `Group`, `Detail`, `Total`, `Chart`, `Pivot`, `Kpi`, `Format`, `Link`, `Image`, `Series`, `ConditionalRule`

**Functions/Methods:**
- `snake_case` — `add_field`, `add_dataset`, `set_format`, `render_html`, `to_excel`, `build_chart`, `build_pivot`
- Fluent builder methods return `self` (or a `Section`) to allow chaining (`report.py`, `section.py`)
- Engine-internal helpers: `_`-prefixed module-level functions — `_enrich`, `_partition`, `_build_group`, `_build_instance`, `_compute_totals_into`, `_apply_order`, `_render_templates`, `_build_kpis` (`aggregation.py`)
- Expression internals: `_walk`, `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`expressions.py`)
- Renderer internals: `_walk`/`_collect` for tree traversal, `_esc`/`_style_attr`/`_full_row`/`_pivot` helpers (`renderers/*.py`)

**Variables:**
- Builder state: `_`-prefixed instance attributes — `self._rows`, `self._fields`, `self._groups`, `self._order`, `self._datasets` (`report.py:27-39`)
- Model context (non-serialized): pydantic `PrivateAttr` with `_`-prefix — `_first_row`, `_header_tpl`, `_footer_tpl` (`models.py:123-126`)
- Module-level constants: `UPPER_SNAKE` — `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`expressions.py:45-47`), `_DANGEROUS_PREFIXES` (`renderers/_sanitize.py:5`)

## Where to Add New Code

**New Feature (e.g., a new aggregation operator):**
- Primary code: add the operator to `_aggregate` in `encino_rpt/aggregation.py:31-45` (and `_value_for` at `aggregation.py:48-62` if it needs expression-aware behavior)
- Validation: `encino_rpt/section.py:40-63` (`Section.total`) if a new `Section` method is needed
- Tests: `tests/test_report.py`

**New Renderer (new output format):**
- Implementation: create `encino_rpt/renderers/<name>.py` with a `<Name>Renderer` class implementing `render(result)` and a recursive `_walk`/`_collect` dispatch over `Group`/`Detail`/`Chart`/`Pivot` (model on `encino_rpt/renderers/csv.py` — the simplest example)
- Registration: add the export to `encino_rpt/renderers/__init__.py`
- Convenience method: add a `to_<name>()` method on `ReportResult` in `encino_rpt/models.py` (with lazy import, per the existing `to_csv` pattern at `models.py:164-175`)
- Tests: `tests/test_report_renderers.py`
- If the format needs a new optional dependency: add an extra in `pyproject.toml:37-39` and import it lazily inside `render()`

**New Expression Function (e.g., `date_diff`):**
- Implementation: add to `_FUNCTIONS` in `encino_rpt/expressions.py:30-42` (whitelist is closed; any name must be added here or registered via `Report.add_function`)
- Tests: `tests/test_report.py` (expression test block, `tests/test_report.py:7-38`)

**New Canonical Node Type (e.g., `Sparkline`):**
- Model: `encino_rpt/models.py` (typed `type: Literal["sparkline"]` discriminator; add to the `Group.children` union)
- Build: `encino_rpt/aggregation.py` (`_build_instance` extras block at `aggregation.py:262-272` pattern)
- Renderers: update every `_walk`/`_collect` in `encino_rpt/renderers/` (see anti-pattern note in `ARCHITECTURE.md`)
- Tests: `tests/test_report.py` + `tests/test_report_renderers.py`

**New Documentation Page:**
- Source: `docs/<name>.md`, registered in `mkdocs.yml` `nav:` (`mkdocs.yml:39-44`) and built via `uv run mkdocs build`

**New CI Step:**
- `.github/workflows/ci.yml` (test/lint gate on PRs and `main`)

## Special Directories

**`encino_rpt/renderers/`:**
- Purpose: Visitor-pattern output renderers + shared helpers
- Generated: No
- Committed: Yes

**`docs/`:**
- Purpose: mkdocs documentation source; `docs/design/10-report.md` is the authoritative design spec
- Generated: No (but `site/` — its build output — is generated and gitignored)
- Committed: Yes

**`prompts/`:**
- Purpose: Internal design analysis notes feeding `docs/design/10-report.md`
- Generated: No
- Committed: No (gitignored — `.gitignore:28`)

**`site/`:**
- Purpose: mkdocs build output
- Generated: Yes (from `docs/` + `mkdocs.yml`)
- Committed: No (`.gitignore:15`)

**`dist/`:**
- Purpose: `uv build` artifacts (`encino_rpt-0.2.0-py3-none-any.whl`, `.tar.gz`)
- Generated: Yes
- Committed: No (`.gitignore:11`)

---

*Structure analysis: 2026-09-16*