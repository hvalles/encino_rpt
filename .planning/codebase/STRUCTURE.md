# Codebase Structure

**Analysis Date:** 2026-09-17

## Directory Layout

```
report/                              # repo root (win32 local dev; CI runs ubuntu-latest)
├── encino_rpt/                      # the library (single importable package)
│   ├── __init__.py                  # public API re-exports (15 names)
│   ├── report.py                    # fluent `Report` builder
│   ├── section.py                   # `Section` facade for a cut
│   ├── _specs.py                    # internal `*Spec` dataclasses (builder intent)
│   ├── aggregation.py               # engine: enrich → group tree → totals → Result
│   ├── expressions.py               # safe AST expression evaluator (no eval)
│   ├── template.py                  # `{{token}}` interpolation for header/footer/URLs
│   ├── charts.py                    # derive `Chart` labels/series from data
│   ├── pivot.py                     # cross-tab `Pivot` builder
│   ├── readers.py                   # `Reader` protocol + registry + built-in readers
│   ├── models.py                    # canonical stdlib @dataclass tree (13 models)
│   ├── _serialize.py                # stdlib JSON round-trip (type-discriminated unions)
│   └── renderers/                   # visitor-style renderers
│       ├── __init__.py              # re-exports the 7 renderer classes
│       ├── _walk.py                 # shared iterative tree traversal generator
│       ├── _format.py               # format_value / excel_number_format
│       ├── _sanitize.py             # OWASP formula-injection mitigation
│       ├── html.py                  # HtmlRenderer
│       ├── excel.py                 # ExcelRenderer (openpyxl, optional)
│       ├── csv.py                   # CsvRenderer
│       ├── text.py                  # TextRenderer
│       ├── markdown.py              # MarkdownRenderer
│       ├── json.py                  # JsonRenderer (schema_version "1.0")
│       └── pdf.py                   # PdfRenderer (reportlab, optional)
├── tests/                           # pytest suite
│   ├── test_report.py               # builder + engine + serialization round-trip
│   ├── test_report_renderers.py     # all 7 renderers
│   ├── test_readers.py              # multi-format readers
│   ├── test_security.py             # formula/expression injection defenses
│   └── test_perf_smoke.py           # performance smoke tests
├── docs/                            # mkdocs source (Spanish)
│   ├── index.md · guide.md · getting-started.md · api.md · security.md
│   └── design/10-report.md          # design rationale
├── .github/workflows/               # CI (test/quality), docs deploy, PyPI publish
├── .planning/                       # GSD planning artifacts (excluded from ruff/mypy)
│   ├── PROJECT.md · ROADMAP.md · STATE.md · STRATEGY.md · REQUIREMENTS.md · config.json
│   └── codebase/                    # ← this map (ARCHITECTURE.md, STRUCTURE.md, ...)
├── site/                            # built mkdocs output (generated; committed)
├── dist/                            # built wheels/sdists (0.2.0, 0.2.2, 0.3.0)
├── prompts/                         # historical analysis prompts (not source)
├── mkdocs.yml                       # docs config
├── pyproject.toml                   # build/project/tool config (hatchling)
├── uv.lock                          # pinned dependency lockfile
├── LICENSE                          # MIT
├── README.md
└── AGENTS.md                        # GSD project context (stack/conventions/arch)
```

## Directory Purposes

**`encino_rpt/`:**
- Purpose: The entire library — the single installable package (`[tool.hatch.build.targets.wheel] packages = ["encino_rpt"]`, `pyproject.toml:5-6`).
- Contains: builder, engine, canonical models, serialization, readers, and renderers.
- Key files: `report.py`, `aggregation.py`, `models.py`, `_serialize.py`, `readers.py`, `renderers/`.

**`encino_rpt/renderers/`:**
- Purpose: All concrete output formats, sharing the `walk()` traversal and formatting/sanitization helpers.
- Contains: 7 `*Renderer` classes + 3 private helper modules (`_walk.py`, `_format.py`, `_sanitize.py`).
- Key files: `html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `markdown.py`, `_walk.py`.

**`tests/`:**
- Purpose: pytest suite covering builder/engine, renderers, readers, security, and performance smoke tests.
- Contains: 5 test modules (~1,684 lines).
- Key files: `test_report.py`, `test_report_renderers.py`, `test_readers.py`, `test_security.py`, `test_perf_smoke.py`.

**`docs/`:**
- Purpose: mkdocs (material, Spanish) source; built to `site/` and deployed to GitHub Pages.
- Contains: guides, API reference, security notes, and a design doc.
- Key files: `index.md`, `guide.md`, `api.md`, `security.md`, `design/10-report.md`.

**`.github/workflows/`:**
- Purpose: CI (`ci.yml` — test + quality), docs deploy (`docs.yml`), PyPI publish (`publish.yml`).
- Key files: `ci.yml`, `docs.yml`, `publish.yml`.

**`.planning/`:**
- Purpose: GSD planning/execution artifacts (roadmap, state, phases, strategy).
- Contains: `PROJECT.md`, `ROADMAP.md`, `STATE.md`, `STRATEGY.md`, `REQUIREMENTS.md`, `config.json`, `phases/`, `codebase/`.
- Key files: `PROJECT.md`, `ROADMAP.md`, `STATE.md`, `codebase/ARCHITECTURE.md`.

**`site/` and `dist/`:**
- Purpose: Generated build artifacts (mkdocs HTML, wheels/sdists). `site/` is committed (for GitHub Pages); `dist/` contains released wheels/sdists.
- Key files: `site/index.html`, `dist/encino_rpt-0.3.0-py3-none-any.whl`.

## Key File Locations

**Entry Points:**
- `encino_rpt/__init__.py`: public API — re-exports 15 names via `__all__` (`__init__.py:21-37`); `Section` intentionally NOT exported.
- `encino_rpt/report.py:426-434` (`Report.run`): materializes the tree.
- `encino_rpt/report.py:44-90` (`Report.read`/`register_reader`): multi-format input.
- `encino_rpt/models.py:224-439` (`ReportResult.render_html`/`to_csv`/`to_text`/`to_markdown`/`to_excel`/`to_json`/`to_pdf` + `iter_*`): renderer delegates.
- `encino_rpt/readers.py:350-371` (`read`): reader dispatch.

**Configuration:**
- `pyproject.toml`: hatchling build (`[build-system]`, `pyproject.toml:1-6`), project metadata (`[project]`, `:8-31`), optional extras `excel`/`pdf` (`:33-35`), dependency groups `dev`/`docs` (`:45-58`), and tool config for pytest/mypy/ruff/coverage (`:41-84`).
- `mkdocs.yml`: docs site config.
- `.github/workflows/ci.yml`: CI (test matrix 3.10–3.13 + quality job).
- `uv.lock`: pinned dependency lockfile.

**Core Logic:**
- `encino_rpt/aggregation.py`: the engine — `build()` + all `_*` helpers.
- `encino_rpt/expressions.py`: AST-whitelist expression evaluator.
- `encino_rpt/charts.py` / `encino_rpt/pivot.py`: chart/pivot derivation.
- `encino_rpt/_serialize.py`: stdlib JSON round-trip.

**Model & Serialization:**
- `encino_rpt/models.py`: canonical dataclass tree (13 node types).
- `encino_rpt/_serialize.py`: `to_jsonable` / `from_dict` with `_NODES` type dispatch.

**Readers:**
- `encino_rpt/readers.py`: `Reader` protocol, `_READERS` registry, 6 built-in readers.

**Testing:**
- `tests/`: pytest suite (see `testpaths = ["tests"]`, `pyproject.toml:42`).

## Naming Conventions

**Files:**
- `snake_case.py` modules: `report.py`, `aggregation.py`, `expressions.py`, `readers.py`, `models.py`.
- Leading underscore for internal/private modules: `_specs.py`, `_serialize.py`, and renderer helpers `_walk.py`, `_format.py`, `_sanitize.py`.
- Tests: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_readers.py`, `test_security.py`, `test_perf_smoke.py`.

**Classes:**
- Builder/facade: `Report`, `Section`, `Reader` (Protocol).
- Canonical model dataclasses: `Link`, `Image`, `Format`, `Total`, `Detail`, `Series`, `Chart`, `Pivot`, `ConditionalRule`, `Kpi`, `Group`, `ReportMeta`, `ReportResult`.
- Renderers suffixed `Renderer`: `CsvRenderer`, `ExcelRenderer`, `HtmlRenderer`, `JsonRenderer`, `MarkdownRenderer`, `PdfRenderer`, `TextRenderer`.
- Internal specs suffixed `Spec`: `FieldSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec`, `GroupSpec` (`encino_rpt/_specs.py`).
- Internal reader classes: `_DelimitedReader` (underscore-prefixed), `JsonReader`, `JsonLinesReader`, `TuplesReader`, `ExcelReader` (`encino_rpt/readers.py`).
- Internal trie node `_PathNode` prefixed `_` (`encino_rpt/aggregation.py:270`).

**Functions:**
- Public: `add_function`, `build_chart`, `build_pivot`, `format_value`, `sanitize_csv`, `evaluate`, `render`, `render_template` (imported as `render`), `build`, `walk`, `to_jsonable`, `from_dict`, `register_reader`, `read`.
- Private module-level helpers prefixed `_`: `_build_group_tree`, `_build_group`, `_build_instance`, `_build_path_group`, `_apply_order`, `_compute_totals_into`, `_resolve_deferred`, `_render_templates`, `_build_kpis`, `_enrich`, `_partition`, `_sort_key`, `_is_zero`, `_ordered_unique`, `_assert_hashable`, `_make_path_node`, `_segs`, `_coerce`, `_build` (`_serialize.py`), etc.
- Prefer full words over abbreviations (`_build_path_group`, not `_bld`); `_esc` and `_segs` are the accepted cross-module abbreviations.

**Constants:**
- `SCHEMA_VERSION = "1.0"`, `DEPTH_ERROR` (`encino_rpt/renderers/json.py:9-14`, `_serialize.py:16-19`).
- `_MAX_NODES`, `_MAX_DEPTH`, `_MAX_POW_EXP` (`encino_rpt/expressions.py:46-48`).
- `_READERS` registry (`encino_rpt/readers.py:35`), `_FORMAT_BY_EXT` map (`readers.py:318-325`).
- Operator dispatch tables: `_BINOPS`, `_UNARY`, `_CMP`, `_FUNCTIONS` (`expressions.py:10-43`), `_OPS` (`renderers/html.py:13-20`), `_COLOR_OPS` (`renderers/excel.py:10-17`).
- `_NODES` discriminator map (`encino_rpt/_serialize.py:22-27`).
- Type alias `Child = Detail | Group | Chart | Pivot` (`encino_rpt/aggregation.py:28`).

## Where to Add New Code

**New Report Feature (builder surface):**
- Primary code: add the fluent method to `encino_rpt/report.py` (returning `self` or a `Section`), record intent into a `*Spec` in `encino_rpt/_specs.py`.
- If it's a per-cut feature: expose it on `Section` (`encino_rpt/section.py`), which mutates the matching `GroupSpec`.
- Engine handling: add the logic to `encino_rpt/aggregation.py` (`build()` or a new `_*` helper).
- If it produces a new tree node: add a `@dataclass` with a `type: Literal[...]` discriminator in `encino_rpt/models.py`, and register it in `_NODES` (`encino_rpt/_serialize.py:22-27`) so serialization round-trips.
- Tests: `tests/test_report.py` (builder/engine) or a new `tests/test_<area>.py`.

**New Renderer (output format):**
- Implementation: `encino_rpt/renderers/<name>.py`, a `<Name>Renderer` class that consumes `walk(result.root)` (`encino_rpt/renderers/_walk.py`) and implements `render(result)` + `iter_*`/`write(result, file)`.
- Reuse: `encino_rpt/renderers/_format.py` (`format_value`) and `encino_rpt/renderers/_sanitize.py` where relevant.
- Registration: export the class from `encino_rpt/renderers/__init__.py` (`__all__`, `:11-19`).
- Wiring: add a `ReportResult.to_<name>`/`iter_<name>` convenience method in `encino_rpt/models.py` (lazy-import the renderer).
- Tests: `tests/test_report_renderers.py`.

**New Reader (input format):**
- Implementation: add a reader class in `encino_rpt/readers.py` implementing `read(source, **opts) -> list[dict]`; register it via `register_reader(name, ...)` alongside the built-ins (`readers.py:375-380`).
- Optional-dependency readers: guard the import with a try/except `ImportError` (mirroring `ExcelReader.read`, `readers.py:295-300`).
- Tests: `tests/test_readers.py`.

**New Model/Serialization behavior:**
- Model types: `encino_rpt/models.py`.
- Serialization: `encino_rpt/_serialize.py` (`_NODES`, `_build`, `_coerce`).

**Utilities:**
- Shared cross-format helpers: `encino_rpt/renderers/_format.py` and `_sanitize.py`.
- Shared traversal: `encino_rpt/renderers/_walk.py`.

## Special Directories

**`site/`:**
- Purpose: Built mkdocs output (deployed to GitHub Pages at `https://hvalles.github.io/encino_rpt/`).
- Generated: Yes (by `mkdocs build`).
- Committed: Yes (for Pages hosting).

**`dist/`:**
- Purpose: Built wheel/sdist artifacts (`encino_rpt-0.2.0`, `0.2.2`, `0.3.0`).
- Generated: Yes (by hatchling).
- Committed: Yes (release artifacts; `dist/.gitignore` present).

**`.venv/`, `__pycache__/`, `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.coverage`:**
- Purpose: Local dev environment and caches.
- Generated: Yes.
- Committed: No (gitignored).

**`.planning/`:**
- Purpose: GSD planning artifacts (roadmap, state, phases, codebase map). Excluded from lint/type-check via `extend-exclude` (`pyproject.toml:72`).
- Generated: By GSD workflows.
- Committed: Yes.

**`prompts/`:**
- Purpose: Historical analysis prompt notes (`24.md`, `25.md`, `analisys-10.md`, `analisys-11.md`); not source code.
- Committed: Yes.

---

*Structure analysis: 2026-09-17*
