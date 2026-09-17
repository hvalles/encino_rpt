<!-- refreshed: 2026-09-17 -->
# Architecture

**Analysis Date:** 2026-09-17

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                     Builder / Configuration Layer                    │
│   `Report` (fluent)  ·  `Section` (facade)  ·  `*Spec` dataclasses   │
│   `encino_rpt/report.py`  `encino_rpt/section.py`  `encino_rpt/_specs.py` │
└───────────────┬─────────────────────────────────────────────────────┘
                │  Report.run()  →  aggregation.build(report)
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Aggregation Engine                            │
│  `aggregation.py` (enrich, partition, group tree, totals, deferred,  │
│   order/top/suppress, templates, KPIs)                               │
│  helpers: `expressions.py` `template.py` `charts.py` `pivot.py`      │
└───────────────┬─────────────────────────────────────────────────────┘
                │  builds/writes
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Canonical Model (pydantic v2)                     │
│   `ReportResult` → `Group` → `Detail|Group|Chart|Pivot` + `Kpi`      │
│   `encino_rpt/models.py`  (JSON-serializable, `schema_version`)      │
└───────────────┬─────────────────────────────────────────────────────┘
                │  read by visitors
                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                            │
│   `walk()` (shared traversal) + 7 renderers + `_format`/`_sanitize`  │
│   `encino_rpt/renderers/{html,excel,csv,text,pdf,json,markdown}.py`  │
└─────────────────────────────────────────────────────────────────────┘

Input side (upstream of the builder):
   `Report.read()` / `Report(rows)`  ←  `encino_rpt/readers.py` (Reader protocol + registry)
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs, custom functions/aggregates; `read()`/`register_reader()` classmethods for multi-format input; `run()` materializes the tree | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a cut's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress_zero/page_break) | `encino_rpt/section.py` |
| `FieldSpec`/`GroupSpec`/`TotalSpec`/`ChartSpec`/`PivotSpec`/`KpiSpec` | Internal builder specifications (dataclasses) — NOT part of the canonical tree | `encino_rpt/_specs.py` |
| `Reader` (protocol) + registry | Multi-format input readers (csv/tsv/json/jsonl/tuples/excel + custom); `read()`/`register_reader()`/`get_reader()` + built-in readers | `encino_rpt/readers.py` |
| `evaluate()` | Safe expression evaluator (AST whitelist, no `eval`, anti-DoS limits) | `encino_rpt/expressions.py` |
| `render()` | `{{token}}` template interpolation for header/footer and link/image URLs | `encino_rpt/template.py` |
| `build()` | Orchestrates `run()`: validate, visible columns, row enrichment, group tree, totals, deferred `TOTAL(...)` resolution, template rendering, KPIs → `ReportResult` | `encino_rpt/aggregation.py` |
| `build_chart()` | Derives `Chart.labels`/`series` from already-aggregated child groups or the group's own totals | `encino_rpt/charts.py` |
| `build_pivot()` | Builds a rows × columns cross-tab matrix (`Pivot`) with row/column totals | `encino_rpt/pivot.py` |
| Pydantic models | Canonical serializable tree: `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta` | `encino_rpt/models.py` |
| `walk()` | Shared iterative tree traversal; yields typed `(event, node)` tuples consumed by every renderer | `encino_rpt/renderers/_walk.py` |
| `HtmlRenderer` | Consumes `walk()` → HTML `<table>` with classes, conditional styles, pivot sub-tables, full-document `template` mode | `encino_rpt/renderers/html.py` |
| `ExcelRenderer` | Consumes `walk()` → openpyxl `Worksheet` (optional dep), native charts, `=SUM(...)` formula mode, cell formatting | `encino_rpt/renderers/excel.py` |
| `CsvRenderer` | Consumes `walk()` → flattened CSV with formula-injection sanitization | `encino_rpt/renderers/csv.py` |
| `TextRenderer` | Consumes `walk()` → indented plain text for inspection | `encino_rpt/renderers/text.py` |
| `MarkdownRenderer` | Consumes `walk()` → GFM tables, groups as headers; charts/pivots degrade to text/GFM | `encino_rpt/renderers/markdown.py` |
| `PdfRenderer` | Consumes `walk()` → reportlab PDF bytes (optional dep), span-based layout | `encino_rpt/renderers/pdf.py` |
| `JsonRenderer` | Serializes `ReportResult` to JSON with `schema_version` (`"1.0"`) | `encino_rpt/renderers/json.py` |
| `format_value`/`excel_number_format` | Shared value formatting per `Format` (currency, %, thousands, parens, dates) | `encino_rpt/renderers/_format.py` |
| `sanitize_csv`/`write_excel_cell`/`is_dangerous` | OWASP formula-injection mitigation for CSV/Excel output | `encino_rpt/renderers/_sanitize.py` |

## Pattern Overview

**Overall:** Layered builder → engine → canonical-model → visitor-renderer pipeline.

**Key Characteristics:**
- Fluent builder API returning `self` for chaining (`report.py`, `section.py`); validation raises early.
- Spec objects (`_specs.py`) decouple what the user declared from the canonical output — specs are consumed by `build()` and never appear in the result tree.
- Two-phase total resolution: base totals first, then deferred expressions using `TOTAL("seccion.nombre")` (phase B in `aggregation.py:494-507`).
- Post-processing phase C: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed, before charts/pivots are appended (`aggregation.py:373-401`).
- Pydantic v2 models with typed discriminators (`type: Literal[...]`); the recursive `Group.children` union is resolved via `Group.model_rebuild()` (`models.py:368`).
- Shared iterative `walk()` generator centralizes the visitor traversal that each renderer consumes (`renderers/_walk.py`).
- All renderers expose both a `render()` (materialized) and an `iter_*`/`write()` (streaming) path; `ReportResult` mirrors this with `to_*`/`render_*` and `iter_*`/`file=` methods.
- Lazy imports for all optional renderer dependencies (`openpyxl`, `reportlab`) and for the engine (`aggregation`) / renderers / readers to break import cycles.
- In-memory aggregation engine; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).

## Layers

**Builder / Configuration Layer:**
- Purpose: Declarative configuration of a report plus multi-format input.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`, `encino_rpt/readers.py`.
- Contains: The `Report` builder, the `Section` facade, internal `*Spec` dataclasses, and the `Reader` protocol + registry.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints), and lazily on `encino_rpt/readers.py` (inside `Report.read`) and `encino_rpt/aggregation.py` (inside `Report.run`).
- Used by: application code (see `README.md` examples).

**Aggregation Engine Layer:**
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, `_partition`, `_build_group_tree`, `_build_group`, `_build_instance`, `_build_path_group`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_render_templates`, `_build_kpis`.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:413-421`).

**Canonical Model Layer:**
- Purpose: Typed, JSON-serializable representation of the report result.
- Location: `encino_rpt/models.py`.
- Contains: 13 pydantic models (see Component Responsibilities table).
- Depends on: `pydantic>=2` only.
- Used by: the engine (writes), the renderers (read), and downstream consumers (`model_dump()` / `model_validate()` / `to_json()`).

**Presentation / Renderer Layer:**
- Purpose: Convert the canonical tree to a concrete output format.
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `markdown.py`, `_walk.py`, `_format.py`, `_sanitize.py`).
- Contains: Visitor-style renderer classes + shared walker/formatting/sanitizing helpers.
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras).
- Used by: `ReportResult` convenience methods and end users.

## Data Flow

### Primary Request Path (build a report)

1. **Input** — `Report.read(source, format=...)` (`encino_rpt/report.py:44-78`) delegates to `readers.read()` (`encino_rpt/readers.py:350-371`), which resolves the reader by name or file extension and returns `list[dict]`. `Report(rows)` (`report.py:19`) remains the direct path.
2. **Declare** — fluent builder methods (`group()`, `detail()`, `add_field()`, `total()` via `Section`, `kpi()`, etc.) populate `FieldSpec`/`GroupSpec`/`KpiSpec` instances.
3. **Run** — `Report.run()` (`report.py:413-421`) lazily imports `aggregation.build` and calls `build(self)`.
4. **Build** — `build()` (`aggregation.py:586-621`): `_validate` → `_visible_columns` → `_enrich` (per source) → `_build_group_tree` → `_build_group`/`_build_instance` (partition, totals base, phase-C order/top/suppress, charts/pivots) → `_resolve_deferred` (phase B) → `_render_templates` → `_build_kpis`.
5. **Result** — a `ReportResult` is returned with `meta`, `columns`, `formats`, `styles`, `kpis`, and `root`.

### Secondary Flow (render to a destination)

1. Call `result.to_csv()` / `render_html()` / `to_markdown()` / `to_excel()` / `to_json()` / `to_pdf()` (`encino_rpt/models.py:150-365`) — each lazily imports the matching renderer.
2. Pass `file=` to any text renderer (`html`, `csv`, `text`, `markdown`, `pdf`) to stream directly instead of returning a string/bytes; call `iter_html()` / `iter_csv()` / `iter_text()` / `iter_markdown()` (`models.py:192-315`) to consume fragments lazily.
3. The renderer constructs itself and calls `render(self)` (materialized) or `write(self, file)` (streaming); both delegate to an `iter_*` generator that consumes `walk(root)`.

**State Management:**
- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:29-42`); no module-level mutable state except the reader registry (`_READERS` in `encino_rpt/readers.py:35`).
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:603-604`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl` via pydantic `PrivateAttr` (`encino_rpt/models.py:123-126`).
- A fresh `Report` instance is required per report — `run()` does not reset the builder.

## Key Abstractions

**`ReportResult` (canonical tree):**
- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:136-365`.
- Pattern: pydantic `BaseModel` with typed children (`root: Group`), convenience render methods with lazy imports, `to_json` with `schema_version`.
- Serialization: `model_dump()` / `model_validate()` round-trip verified in `tests/test_report.py`.

**`*Spec` + `Section` (builder spec):**
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:75-93`, `encino_rpt/section.py`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`report.py:347-411`).

**`evaluate()` (safe expression evaluator):**
- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:55-123`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:67-123`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:46-48`).

**`walk()` (shared traversal):**
- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)` + `iter_*`/`write(result, file)`; register it in `encino_rpt/renderers/__init__.py`.

**`Reader` protocol + registry:**
- Purpose: Multi-format input to `list[dict]`, decoupled from `Report`.
- Location: `encino_rpt/readers.py`.
- Pattern: `Reader` is a `typing.Protocol` with `read(source, **opts) -> list[dict]`; `register_reader(name, reader)` mutates the module-level `_READERS` dict; `read()` resolves the name via `_resolve_format` (explicit `format=` or file extension) and dispatches through `get_reader()`. Six built-in readers are registered at import (`readers.py:375-380`).
- Extension: `Report.register_reader(name, reader)` (`report.py:80-90`) delegates here; custom readers are any object with a `read(source, **opts)` method.

**Path-group trie:**
- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:270-331` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

**Public package API:**
- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, Reader, ...`.
- Responsibilities: re-export the builder, canonical model types, and `Reader` protocol; `__all__` lists 15 public names (`__init__.py:21-36`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).

**`Report.run()`:**
- Location: `encino_rpt/report.py:413-421`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.

**`Report.read()` / `Report.register_reader()`:**
- Location: `encino_rpt/report.py:44-90`.
- Triggers: user call to build a `Report` from a file/file-like/raw source, or to register a custom reader.
- Responsibilities: delegate to `encino_rpt/readers.py`.

**`ReportResult` convenience methods:**
- Location: `encino_rpt/models.py:150-365` (`render_html`, `to_csv`, `to_text`, `to_markdown`, `to_excel`, `to_json`, `to_pdf`, plus `iter_html`/`iter_csv`/`iter_text`/`iter_markdown`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

**`readers.read()`:**
- Location: `encino_rpt/readers.py:350-371`.
- Triggers: `Report.read()` or direct `from encino_rpt.readers import read`.
- Responsibilities: resolve the reader name and dispatch to the reader's `read()`.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async. The reader registry `_READERS` (`readers.py:35`) is the only module-level mutable state, and it is write-once-at-import plus user `register_reader` calls.
- **Global state:** `ExcelRenderer` stores transient mutable state on `self` (`_ws`, `_result`, `_formulas`, `_row` — `renderers/excel.py:51-54`), making it non-reentrant across concurrent renders of the same instance. `PdfRenderer` sets `self._normal` during `render` (`renderers/pdf.py:51`).
- **Circular imports:** Avoided via lazy imports. `report.py` imports `aggregation.py` lazily inside `run()` (`report.py:419`) and `readers.py` lazily inside `read()`/`register_reader()` (`report.py:75,88`); `models.py` imports renderers lazily inside convenience methods (`models.py:178-363`). `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`expressions.py`). `ast.parse` node/depth/pow counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`renderers/excel.py:40-46`) and `ExcelReader.read` (`readers.py:295-300`); `reportlab` only inside `PdfRenderer.render` (`renderers/pdf.py:35-48`). All raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **Pydantic forward references:** `Group.children` is a recursive union, resolved with `Group.model_rebuild()` at the bottom of `encino_rpt/models.py:368`.

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

**What happens:** `build()` and its helpers read `report._rows`, `report._datasets`, `report._fields`, `report._groups`, `report._functions`, etc. directly (`aggregation.py:135,168,565-583`).
**Why it's wrong:** The engine depends on the builder's private implementation details; renaming an attribute on `Report` silently breaks aggregation.
**Do this instead:** Keep reading `_`-prefixed attributes in `aggregation.py` only — it is the sole consumer of the builder's internal state, and this coupling is intentional and documented. When adding a new builder feature, add a corresponding read in `_validate`, `_enrich`, or `_build_*` in the same change.

### Charts/pivots appended after phase-C ordering

**What happens:** `node.children = _apply_order(...)` runs first, then charts/pivots are appended with `node.children = node.children + extras` (`aggregation.py:374-401`).
**Why it's wrong:** Ordering/top/suppress must not reorder or drop charts/pivots relative to detail/groups; mixing them would corrupt the document order that `walk()` relies on.
**Do this instead:** Always append charts/pivots after `_apply_order`, exactly as `_build_instance` does. Do not pass `extras` into `_apply_order`.

### Duplicated operator/conditional tables per renderer

**What happens:** `_OPS` (html), `_COLOR_OPS` (excel), and the `_BINOPS`/`_CMP` dicts in `expressions.py` each re-declare the same comparison operators.
**Why it's wrong:** New comparison operators or conditional styles must be added in multiple places, risking divergence.
**Do this instead:** When adding a comparison operator, update both `expressions._CMP` and the renderer `_OPS`/`_COLOR_OPS` tables. Consider extracting a shared table if a third consumer appears.

### Reimplementing tree traversal per renderer

**What happened (historical):** Renderers previously duplicated traversal logic.
**Why it's wrong:** Traversal order bugs (e.g., totals emitted before children, or footer before totals) had to be fixed in every renderer separately.
**Do this instead:** All renderers now consume the single `walk()` generator in `encino_rpt/renderers/_walk.py`. New renderers must import `walk` and handle `group_start`/`group_end`/`detail`/`chart`/`pivot`, never write their own recursion.

## Error Handling

**Strategy:** Fail fast with contextual `ValueError` subclasses; never swallow exceptions in the engine.

- Builder validation: `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:375-376`) and on duplicate cut names (`report.py:377-378`); `section()` raises `KeyError` for undeclared cuts (`report.py:408-410`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:163-164`).
- Reader errors: `get_reader()` raises `ValueError` for unregistered readers (`readers.py:60-63`); `read()` raises `ValueError` when the format can't be resolved (`readers.py:347`); `TuplesReader` raises `ValueError` when `columns` is missing or mismatched (`readers.py:264-273`); JSON/JSONL readers raise `TypeError` for non-list/non-dict payloads.
- Engine context wrapping: `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`aggregation.py:35-44`).
- Expression errors: `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`expressions.py:51-123`).
- Template errors: `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`template.py:20-31`).
- Aggregate errors: `ValueError` for unknown operators (`aggregation.py:69`); `AggregationError` for unregistered custom aggregates (`aggregation.py:87`, `574-575`).
- Optional dependency errors: `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:44-46`, `renderers/pdf.py:45-48`, `readers.py:297-300`) — covered by `pytest.importorskip` in tests.
- Serialization errors: `JsonRenderer.to_dict`/`render` convert deep-recursion `RecursionError` into a controlled `ValueError` (`renderers/json.py:32-55`).
- Aggregation never catches exceptions: a failing expression propagates up through `run()` to the caller.

## Cross-Cutting Concerns

**Logging:** None — no `logging` module usage anywhere in `encino_rpt/`; the library is silent and relies on raised exceptions.
**Validation:** Split between the builder (`report.py`, `section.py` — immediate) and `_validate` (`aggregation.py:564-583` — at `run()` time, for cross-cutting checks like undeclared `source`/`parent`).
**Authentication:** Not applicable — pure in-memory library; no network, no auth.
**Security:** Formula-injection mitigation centralizes in `renderers/_sanitize.py`; HTML escaping in `renderers/html.py` (`_esc`, `_SAFE_PROP`, `_UNSAFE_VALUE`); expression safety in `expressions.py` (no `eval`, AST whitelist, DoS caps).
**Streaming:** Every text renderer exposes `render()` (materialized), `iter_*` (generator), and `write(result, file)`; `ReportResult` mirrors with `to_*`/`render_*`, `iter_*`, and `file=` params.

---

*Architecture analysis: 2026-09-17*
