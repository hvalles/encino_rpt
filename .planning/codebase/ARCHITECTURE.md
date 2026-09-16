<!-- refreshed: 2026-09-16 -->
# Architecture

**Analysis Date:** 2026-09-16

## System Overview

`encino_rpt` is a financial report generator over `list[dict]`. It converts rows
materialized from a DB (the output of `fetch_all`/`fetch_many`/`paginate`) into a
**canonical typed tree** decoupled from the output destination, then renders that
tree to HTML, Excel, CSV, PDF, or plain text. The package is designed as an
additive, standalone project that consumes `encinorm` output only (see
`docs/design/10-report.md` §1, §10); it never generates SQL itself.

```text
┌──────────────────────────────────────────────────────────────────┐
│                     Input: list[dict] rows + params              │
│              (materialized from DB, no SQL generated here)       │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Builder Layer (fluent API)                     │
│   Report      `encino_rpt/report.py`       (accumulates specs)   │
│   Section     `encino_rpt/section.py`      (mutates GroupSpec)   │
│   Specs       `encino_rpt/_specs.py`       (dataclasses)         │
├──────────────────────────────────────────────────────────────────┤
│              Engine: `report.run()` → `aggregation.build()`      │
│   `encino_rpt/aggregation.py`   enrich rows → group tree →       │
│   totals (base + phase B deferred) → charts/pivots → order/      │
│   top/suppress (phase C) → templates → KPIs                      │
│   helpers: `expressions.py` (safe eval)  `template.py` ({{}})    │
│            `charts.py` (Chart nodes)     `pivot.py` (Pivot)      │
├──────────────────────────────────────────────────────────────────┤
│                   Canonical Model (pydantic v2)                  │
│   `encino_rpt/models.py`  ReportResult + node types,             │
│   serializable via `model_dump()` (JSON)                         │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                 Presentation Layer (visitor pattern)             │
│   `encino_rpt/renderers/`  html.py  excel.py  csv.py  text.py    │
│   pdf.py  (+ shared `_format.py`, `_sanitize.py`)                │
│   Invoked lazily from `ReportResult.render_html/to_*` methods    │
└──────────────────────────────────────────────────────────────────┘
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

**Overall:** Pipeline: builder → engine → canonical data model → renderer visitor.

The canonical `ReportResult` is the contract between the engine and the
presentation layer. Renderers never mutate the tree; they are pure walkers
(visitor pattern). `ReportResult.render_html`/`to_*` are convenience methods
(`encino_rpt/models.py:150-214`) that lazily import their renderer so optional
dependencies (`openpyxl`, `reportlab`) are never loaded unless used.

**Key Characteristics:**
- Fluent builder API returning `self` for chaining (`report.py`, `section.py`)
- Spec objects (`_specs.py`) decouple what the user declared from the canonical output
- Two-phase total resolution: base totals first, then deferred expressions using `TOTAL("seccion.nombre")` (phase B)
- Post-processing phase C: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed (`aggregation.py:277-287`)
- Pydantic v2 models with typed discriminators (`type: Literal[...]`) for polymorphic children
- Lazy imports for all optional renderer dependencies
- In-memory aggregation engine (scalability note in design doc §11: heavy aggregates delegate to SQL `ROLLUP`/`CUBE`)

## Layers

**Builder Layer (public API):**
- Purpose: Declarative configuration of a report
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`
- Contains: The `Report` builder, the `Section` facade, and internal `*Spec` dataclasses
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints)
- Used by: application code (see README examples)

**Engine Layer (aggregation):**
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`
- Location: `encino_rpt/aggregation.py` (with helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`)
- Contains: `build(report)`, partitioning, group-tree construction, total computation, template resolution, KPI computation
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`
- Used by: only `Report.run()` (`encino_rpt/report.py:278-286`)

**Canonical Model Layer:**
- Purpose: Typed, JSON-serializable representation of the report result
- Location: `encino_rpt/models.py`
- Contains: 13 pydantic models (see Component Responsibilities table)
- Depends on: `pydantic>=2` only
- Used by: the engine (writes), the renderers (read), and downstream consumers (`model_dump()` / `model_validate()`)

**Presentation Layer (renderers):**
- Purpose: Convert the canonical tree to a concrete output format
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `_format.py`, `_sanitize.py`)
- Contains: Visitor-style renderer classes + shared formatting/sanitizing helpers
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras)
- Used by: `ReportResult` convenience methods and end users

## Data Flow

### Primary Request Path (build a report)

1. **User constructs a `Report`**: `Report(rows, params, title)` stores copies of rows/params (`encino_rpt/report.py:19-39`). Fluent calls accumulate declarations: `add_field`/`link`/`image` → `self._fields` (`report.py:145-208`), `detail` → `self._detail` (`report.py:211-222`), `group` → `self._groups` + `self._order` + returns a new `Section` (`report.py:224-259`), `section(name)` re-opens an existing spec (`report.py:261-276`).
2. **`run()` delegates to `build(self)`** (`encino_rpt/report.py:278-286` → `encino_rpt/aggregation.py:381`).
3. **`build()` computes visible columns** from `detail` + `after=` field placement (`aggregation.py:370-378`).
4. **Rows are enriched per source**: computed fields evaluated via `evaluate()`, links/images built via templates, cumulative (`cumulative="sum"`) accumulators applied (`aggregation.py:90-113`). Datasets registered with `add_dataset` are enriched independently (`aggregation.py:385-387`).
5. **Group tree is assembled** from `GroupSpec`s; the first declared spec with `columns=None`/`path=None` becomes the root, or an implicit `global` group is created (`aggregation.py:117-137`).
6. **Group nodes are built recursively**: `_build_group` partitions rows by the group's columns (`_partition`, `aggregation.py:140-153`); `_build_instance` creates `Group` nodes, attaches `Detail` children (or child groups), computes totals, then appends `Chart`/`Pivot` nodes via `build_chart`/`build_pivot` (`aggregation.py:234-274`). Path-based groups (`group(..., path=...)`) recurse by data-driven hierarchy levels (`aggregation.py:182-231`).
7. **Totals**: base totals computed immediately; totals whose expression contains `TOTAL(` are deferred to phase B and accumulated into a registry keyed `"<group>.<total_name>"` (`aggregation.py:166-179`, resolved at `aggregation.py:330-334` with a `TOTAL` function injected into the evaluator).
8. **Phase C**: `order_by`/`top_n`/`suppress_zero` reorder/filter each group's children (`aggregation.py:277-326`).
9. **Templates rendered last**: header/footer interpolated with context = first row + group key + `total.*` registry values + `params` (`aggregation.py:338-354`).
10. **KPIs computed** from `KpiSpec`s (`aggregation.py:357-367`) and the final `ReportResult` returned with meta, columns, formats, styles, kpis, and root group (`aggregation.py:399-406`).

### Secondary Flow (render to a destination)

1. Caller invokes `result.render_html(...)` / `to_csv()` / `to_text()` / `to_excel()` / `to_pdf()` on the `ReportResult` (`encino_rpt/models.py:150-214`).
2. Each method lazily imports its renderer class and calls `render(result)` — e.g. `HtmlRenderer(classes=..., repeat_header=...).render(self)` (`models.py:160-162`).
3. The renderer walks the tree: each `_walk`/`_collect` dispatches on `isinstance(node, Group | Detail | Chart | Pivot)` (`renderers/html.py:51-76`, `excel.py:72-113`, `csv.py:35-58`, `text.py:27-55`, `pdf.py:77-97`).
4. Shared `format_value(...)` applies column/total `Format`s and `excel_number_format(...)` translates them for Excel (`renderers/_format.py`); `_sanitize.py` guards against formula injection.
5. Alternative consumer: `result.model_dump()` → JSON canonical form; `ReportResult.model_validate(data)` restores it (tested in `tests/test_report.py:235-243`).

**State Management:**
- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:27-39`); there is no module-level mutable state.
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:381-397`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl` via pydantic `PrivateAttr` (`encino_rpt/models.py:123-126`).
- A fresh `Report` instance is required per report — `run()` does not reset the builder, so re-running `run()` re-executes the full aggregation.

## Key Abstractions

**`ReportResult` (canonical tree root):**
- Purpose: The serializable contract between engine and presentation; pure data
- Location: `encino_rpt/models.py:136-214`
- Pattern: pydantic `BaseModel` with typed children (`root: Group`), convenience render methods with lazy imports
- Serialization: `model_dump()` / `model_validate()` round-trip verified in `tests/test_report.py:235-243`

**`GroupSpec` / `Section`:**
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it
- Location: `encino_rpt/_specs.py:77-97`, `encino_rpt/section.py`
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`report.py:261-276`)

**Expression evaluator (`evaluate`):**
- Purpose: Computed fields, conditional totals, and ordering expressions
- Location: `encino_rpt/expressions.py:54-60`
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:63-109`); no `eval`
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:45-47`)

**Renderer visitor interface:**
- Purpose: Uniform tree walking across output formats
- Location: `encino_rpt/renderers/` — each renderer implements `render(result)` and a recursive `_walk`/`_collect(node, ...)`
- Pattern: dispatch by `isinstance` over `Group` / `Detail` / `Chart` / `Pivot`; KPIs and column header handled before walking
- Extension: add a new renderer class implementing the same `render(result)` contract; register it in `encino_rpt/renderers/__init__.py`

**Specs vs. canonical models:**
- Purpose: Separate what the user declared (`FieldSpec`, `GroupSpec`, `TotalSpec`, `ChartSpec`, `PivotSpec`, `KpiSpec` — `_specs.py`) from the produced output (`Total`, `Group`, `Chart`, `Pivot`, `Kpi`, `Detail` — `models.py`)
- Pattern: engine maps specs → models during `build()`; specs never appear in the output tree

## Entry Points

**Public package API:**
- Location: `encino_rpt/__init__.py`
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, ...`
- Responsibilities: re-export the builder and the canonical model types; `__all__` lists 14 public names (`__init__.py:20-34`)

**`Report.run()`:**
- Location: `encino_rpt/report.py:278-286`
- Triggers: user call after declaring the report
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`

**`ReportResult` render methods:**
- Location: `encino_rpt/models.py:150-214` (`render_html`, `to_csv`, `to_text`, `to_excel`, `to_pdf`)
- Triggers: end-user call on the result
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree

**CLI / server:** None. This is a library package only (no console scripts in `pyproject.toml`).

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

**What happens:** `aggregation.build(report)` reads private attributes directly — `report._rows`, `report._fields`, `report._groups`, `report._order`, `report._functions`, `report._aggregates`, `report._datasets`, `report._kpis`, `report._params`, `report._title`, `report._formats`, `report._styles`, `report._detail` (`encino_rpt/aggregation.py:91,96,118-122,359,382-406`).
**Why it's wrong:** The engine depends on the builder's internal representation; changing an attribute name or storage shape in `Report` silently breaks `build()`. There is no interface boundary between the two layers.
**Do this instead:** Either keep `Report` and `build()` in the same module as a deliberate private pair (documented as such), or expose an explicit read-only "spec bundle" object that `build()` consumes — the specs in `_specs.py` are already the right shape.

### Charts/pivots appended after phase-C ordering

**What happens:** `_build_instance` appends `Chart`/`Pivot` extras to `node.children` *after* `_apply_order` ran (`encino_rpt/aggregation.py:260-272`). Tests assert this position explicitly (`tests/test_report.py:169`).
**Why it's wrong:** The order/top/suppress operations silently don't apply to chart/pivot nodes; a caller using `order_by(...).top(2)` may be surprised that charts/pivots remain and appear last.
**Do this instead:** Document the behavior as intended (extras always last) in the `Section` docstrings, or re-run ordering over the full child list after extras are appended.

### Duplicated visitor dispatch and operator tables per renderer

**What happens:** Each renderer repeats the same `isinstance` dispatch skeleton (`renderers/html.py:51-76`, `excel.py:72-113`, `csv.py:35-58`, `text.py:27-55`, `pdf.py:77-97`) and its own `_OPS`/`_COLOR_OPS` comparison table (`html.py:11-18`, `excel.py:9-16`).
**Why it's wrong:** Adding a node type or a conditional operator requires touching every renderer plus the shared tables; drift is easy (e.g., CSV/Text don't apply conditional styles).
**Do this instead:** Extract a shared `apply_conditional(value, rules, column)` helper (like `_format.py` already does for value formatting) and consider a base `_walk` skeleton that renderers customize via hooks.

## Error Handling

**Strategy:** Exceptions are raised eagerly during builder/engine phases (fail fast), and optionally skipped at render time only when dependencies are missing (with a translated `ImportError`).

**Patterns:**
- Builder validation: `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:247-248`); `section()` raises `KeyError` for undeclared cuts (`report.py:274-275`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:130-131`).
- Expression errors: `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`expressions.py:50-52,58-59,69,73,77,81,87,93,98,101,104,106,109`).
- Template errors: `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params (`template.py:23-26`).
- Aggregate errors: `ValueError` for unknown operators (`aggregation.py:45`).
- Optional dependency errors: `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:44-45`, `renderers/pdf.py:39-40`) — covered by `pytest.importorskip` in tests.
- Aggregation never catches exceptions: a failing expression propagates up through `run()` to the caller.

## Cross-Cutting Concerns

**Logging:** None — no `logging` module usage anywhere in the package. Errors surface as exceptions.
**Validation:** Input validation is minimal by design (trusts `list[dict]` rows); the only schema validation is at the output boundary via pydantic models with `Literal` discriminators.
**Authentication:** None — the library is a pure in-memory processor; it never touches the network.
**Security:**
- Expression sandbox: AST whitelist, no `eval` (`encino_rpt/expressions.py`)
- Formula injection protection: CSV/Excel output sanitized (`encino_rpt/renderers/_sanitize.py`, tested in `tests/test_security.py:9-28`)
- HTML escaping of all emitted text and style-property whitelist regex `_SAFE_PROP` (`renderers/html.py:20,104-105,108-124`, tested in `tests/test_security.py:45-54`)
- Anti-DoS limits on expression size/depth/exponent (`expressions.py:45-47`, tested in `tests/test_security.py:31-42`)

---

*Architecture analysis: 2026-09-16*