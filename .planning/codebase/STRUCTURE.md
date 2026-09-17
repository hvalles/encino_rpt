# Codebase Structure

**Analysis Date:** 2026-09-17

## Directory Layout

```
report/                        # Repo root (encino-rpt library)
├── encino_rpt/                # The package (pure Python, stdlib + optional deps)
│   ├── __init__.py            # Public barrel (15 exported names)
│   ├── report.py              # Fluent `Report` builder
│   ├── section.py             # `Section` facade over a GroupSpec
│   ├── _specs.py              # Internal *Spec dataclasses (builder state)
│   ├── readers.py             # Multi-format input readers + `Reader` protocol
│   ├── aggregation.py         # The engine: build(), group tree, totals, KPIs
│   ├── expressions.py         # Safe AST-whitelist expression evaluator
│   ├── template.py            # `{{token}}` interpolation
│   ├── charts.py              # Chart derivation from aggregated data
│   ├── pivot.py               # Cross-tab (rows × columns) builder
│   ├── models.py              # Canonical tree (stdlib dataclasses)
│   ├── _serialize.py          # to_jsonable / from_dict (JSON round-trip)
│   └── renderers/             # Visitor-style output renderers
│       ├── __init__.py        # Barrel (7 renderer classes)
│       ├── _walk.py           # Shared iterative tree traversal
│       ├── _format.py         # Value formatting + Excel number format
│       ├── _sanitize.py       # OWASP formula-injection mitigation
│       ├── html.py            # HtmlRenderer
│       ├── excel.py           # ExcelRenderer (openpyxl, optional)
│       ├── csv.py             # CsvRenderer
│       ├── text.py            # TextRenderer
│       ├── markdown.py        # MarkdownRenderer
│       ├── pdf.py             # PdfRenderer (reportlab, optional)
│       └── json.py            # JsonRenderer (schema versioned)
├── tests/                     # pytest suite (one file per area)
├── docs/                      # mkdocs source (api, guide, security, getting-started)
│   └── design/                # Design docs (10-report.md)
├── .github/workflows/         # ci.yml, docs.yml, publish.yml
├── .planning/                 # GSD planning artifacts (PROJECT/ROADMAP/STATE/…)
│   └── codebase/              # Codebase map documents (this file)
├── pyproject.toml             # hatchling build + project metadata + tool config
├── uv.lock                    # Pinned dependency lockfile
├── README.md                  # Project readme
├── mkdocs.yml                 # Docs config (material theme, Spanish)
└── LICENSE                    # MIT
```

## Directory Purposes

**`encino_rpt/` (the package):**
- Purpose: The entire library — builder, engine, canonical model, serialization, and renderers.
- Contains: 12 top-level modules + the `renderers/` subpackage.
- Key files: `report.py`, `aggregation.py`, `models.py`, `_serialize.py`, `readers.py`.

**`encino_rpt/renderers/`:**
- Purpose: Convert the canonical `ReportResult` tree to concrete output formats via a shared `walk()` visitor.
- Contains: 7 renderer classes + 3 shared helpers (`_walk.py`, `_format.py`, `_sanitize.py`).
- Key files: `_walk.py`, `html.py`, `excel.py`, `json.py`.

**`tests/`:**
- Purpose: pytest suite organized by concern; coverage ≥80% enforced in CI.
- Contains: `test_report.py` (builder/engine), `test_report_renderers.py`, `test_readers.py`, `test_security.py`, `test_perf_smoke.py`.

**`docs/`:**
- Purpose: mkdocs-material source (Spanish). Reference docs are generated via mkdocstrings (Google-style docstrings).
- Contains: `api.md`, `guide.md`, `security.md`, `getting-started.md`, `index.md`, `design/10-report.md`.

**`.github/workflows/`:**
- Purpose: CI (test matrix 3.10–3.13 + quality), docs build/deploy to Pages, package publish to PyPI/TestPyPI.

**`.planning/`:**
- Purpose: GSD workflow artifacts (`PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, `STRATEGY.md`, `config.json`, `phases/`, `codebase/`). Excluded from ruff (`pyproject.toml:72`) and git-committed.

## Key File Locations

**Entry Points:**
- `encino_rpt/__init__.py`: Public API barrel; `__all__` exports 15 names.
- `encino_rpt/report.py:426` (`Report.run()`): materializes the report tree.
- `encino_rpt/report.py:44` (`Report.read()`): multi-format input factory.
- `encino_rpt/readers.py:350` (`read()`): reader dispatch entry point.

**Configuration:**
- `pyproject.toml`: hatchling build, project metadata (`version = "0.2.2"`), optional extras (`excel`, `pdf`), dev/docs dependency groups, and tool configs for pytest/mypy/ruff/coverage.
- `mkdocs.yml`: docs site config.
- `.github/workflows/ci.yml`: CI with `test` + `quality` jobs and `--cov-fail-under=80`.

**Core Logic:**
- `encino_rpt/aggregation.py`: the aggregation engine (`build()`, group tree, totals, deferred `TOTAL(...)`, KPIs, templates).
- `encino_rpt/expressions.py`: safe expression evaluator.
- `encino_rpt/models.py`: canonical dataclass tree + `ReportResult` convenience methods.
- `encino_rpt/_serialize.py`: JSON round-trip serialization.

**Testing:**
- `tests/test_report.py`, `tests/test_report_renderers.py`, `tests/test_readers.py`, `tests/test_security.py`, `tests/test_perf_smoke.py`.

## Naming Conventions

**Files:**
- `snake_case.py` for public modules (`report.py`, `section.py`, `aggregation.py`, `pivot.py`, `charts.py`, `expressions.py`, `template.py`, `models.py`, `readers.py`).
- Leading underscore for internal modules: `_specs.py`, `_serialize.py`, and `renderers/_walk.py`, `renderers/_format.py`, `renderers/_sanitize.py`.
- Tests: `tests/test_<area>.py`.

**Classes:**
- `PascalCase` for public models/builders: `Report`, `Section`, `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta`, `Reader`.
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `MarkdownRenderer`, `PdfRenderer`, `TextRenderer`.
- Internal spec dataclasses suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (`encino_rpt/_specs.py`).
- Internal reader classes: `_DelimitedReader` (leading `_`), `JsonReader`, `JsonLinesReader`, `TuplesReader`, `ExcelReader`.
- Internal helper class `_PathNode` (trie node) prefixed `_` (`encino_rpt/aggregation.py:270`).

**Functions/Variables:**
- `snake_case`: `add_function`, `build_chart`, `format_value`, `sanitize_csv`, `evaluate`, `build_pivot`, `render`, `build`, `walk`, `_coerce`, `register_reader`.
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_apply_order`, `_compute_totals_into`, `_enrich`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_make_path_node`, `_coerce`, `_full_row`, `_total_row`, `_cell_attrs`, `_style_attr`, `_md_escape`, `_md_url`, `_md_cell`, `_md_table`, `_esc`, `_walk`.
- Private instance attributes prefixed `_`, set in `__init__`: `self._rows`, `self._functions`, `self._groups`, `self._fields`, `self._detail`, `self._order`, `self._formats`, `self._styles`, `self._datasets`, `self._kpis` (`encino_rpt/report.py:29-42`); `self._spec` (`encino_rpt/section.py:11-12`); `self._delimiter` (`encino_rpt/readers.py:165`).
- Non-serialized context on `Group` set in `__post_init__`: `_first_row`, `_header_tpl`, `_footer_tpl` (`encino_rpt/models.py:136-138`).
- `UPPER_SNAKE` module-level constants: `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`expressions.py:46-48`), `_TOKEN` (`template.py:7`), `_DANGEROUS_PREFIXES`, `_LEADING_TRIM` (`_sanitize.py:7-9`), `_SAFE_PROP`, `_UNSAFE_VALUE` (`html.py:22-23`), `SCHEMA_VERSION = "1.0"` (`json.py:9`), `_READERS` (`readers.py:35`), `_FORMAT_BY_EXT` (`readers.py:318-325`), `_NODES` (`_serialize.py:17-22`).

## Where to Add New Code

**New Feature (builder method):**
- Primary code: add the method to `encino_rpt/report.py` (or `encino_rpt/section.py` for a cut's presentation); if it needs new declaration state, add a field to the matching `*Spec` dataclass in `encino_rpt/_specs.py`.
- Engine wiring: consume the spec in `encino_rpt/aggregation.py` (`build()` / `_build_instance` / `_compute_totals_into`).
- Tests: `tests/test_report.py`.

**New Component/Model type:**
- Define the dataclass in `encino_rpt/models.py`.
- If it appears inside `Group.children`, add it to the `_NODES` dispatch map in `encino_rpt/_serialize.py:17-22` and the `Child` union in `encino_rpt/aggregation.py:28`.
- Handle the new event in `encino_rpt/renderers/_walk.py` and in every renderer's event loop.

**New Renderer:**
- Implementation: `encino_rpt/renderers/<name>.py` — subclass the visitor pattern, consume `walk()` (`encino_rpt/renderers/_walk.py`), and implement `render(result)` + `iter_*`/`write(result, file)`.
- Register it in `encino_rpt/renderers/__init__.py` (`__all__`).
- Optional: add a `to_<name>`/`iter_<name>` convenience method to `ReportResult` in `encino_rpt/models.py` (with a lazy import).
- Tests: `tests/test_report_renderers.py`.

**New Input Reader:**
- Implementation: `encino_rpt/readers.py` — add a class with `read(source, **opts) -> list[dict]`, then `register_reader("name", ...)` at module bottom (`readers.py:375-380`); add its extension to `_FORMAT_BY_EXT` if relevant.
- Tests: `tests/test_readers.py`.

**Utilities / shared helpers:**
- Value formatting: `encino_rpt/renderers/_format.py`.
- Formula-injection sanitization: `encino_rpt/renderers/_sanitize.py`.

## Special Directories

**`.venv/`:**
- Purpose: Local virtualenv (uv).
- Generated: Yes.
- Committed: No (gitignored).

**`dist/`:**
- Purpose: Built wheel/sdist artifacts (currently `encino_rpt-0.2.0-*`, behind the `0.2.2` in `pyproject.toml`).
- Generated: Yes (via `uv build` in CI).
- Committed: No (gitignored).

**`site/`:**
- Purpose: Built mkdocs site output.
- Generated: Yes.
- Committed: No.

**`__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/`, `.coverage`:**
- Purpose: Python/tooling caches and coverage data.
- Generated: Yes.
- Committed: No.

---

*Structure analysis: 2026-09-17*
