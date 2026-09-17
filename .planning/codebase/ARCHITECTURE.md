<!-- refreshed: 2026-09-17 -->
# Architecture

**Analysis Date:** 2026-09-17

## System Overview

`encino-rpt` (`v0.3.0`) is a pure-Python financial reporting **library** (not an application): it consumes an already-materialized `list[dict]` and produces a canonical, JSON-serializable tree (`ReportResult`) that optional renderers turn into HTML/Excel/CSV/PDF/text/Markdown/JSON. The public entry point is a fluent builder (`Report`) that validates early and delegates execution to an in-memory aggregation engine.

```text
┌──────────────────────────────────────────────────────────────────────┐
│                        DECLARATIVE LAYER (builder)                     │
│  Report  — fluent builder: rows, params, computed fields, links,      │
│            images, detail, groups, formats, styles, datasets, KPIs    │
│            `encino_rpt/report.py`                                      │
│  Section — facade mutating one cut's GroupSpec (header/footer/total/  │
│            chart/pivot/order/top/suppress_zero/page_break)            │
│            `encino_rpt/section.py`                                     │
│  *Spec   — internal dataclasses recording declared config             │
│            `encino_rpt/_specs.py`                                      │
│  Reader  — Protocol + registry for multi-format input                 │
│            `encino_rpt/readers.py`                                     │
└───────────────┬───────────────────────────────────────────────────────┘
                │  Report.run()  (lazy import)
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          ENGINE LAYER                                  │
│  build() — validate → visible columns → enrich rows → group tree      │
│            → totals (phase A) → deferred TOTAL(...) (phase B)         │
│            → order/top/suppress_zero (phase C) → templates → KPIs     │
│            `encino_rpt/aggregation.py`                                 │
│  helpers: evaluate() `expressions.py` · render() `template.py`        │
│           build_chart() `charts.py` · build_pivot() `pivot.py`        │
└───────────────┬───────────────────────────────────────────────────────┘
                │  writes
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          MODEL LAYER                                   │
│  Canonical tree as stdlib @dataclass (13 node types)                  │
│            `encino_rpt/models.py`                                      │
│  Round-trip (de)serialization via type-discriminated unions           │
│            `encino_rpt/_serialize.py`                                  │
└───────────────┬───────────────────────────────────────────────────────┘
                │  ReportResult.to_* / render_* (lazy import)
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         RENDERER LAYER                                 │
│  Shared traversal walk() → typed (event, node) stream                 │
│            `encino_rpt/renderers/_walk.py`                             │
│  Html · Excel · Csv · Text · Pdf · Json · Markdown                    │
│            `encino_rpt/renderers/`                                     │
│  Shared helpers: format_value() `_format.py` · OWASP sanitize `_sanitize.py`
└───────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs, custom functions/aggregates; `read()`/`register_reader()` classmethods for multi-format input; `run()` materializes the tree | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a cut's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress_zero/page_break) | `encino_rpt/section.py` |
| `FieldSpec`/`GroupSpec`/`TotalSpec`/`ChartSpec`/`PivotSpec`/`KpiSpec` | Internal builder specifications (dataclasses) — NOT part of the canonical tree | `encino_rpt/_specs.py` |
| `Reader` (protocol) + registry | Multi-format input readers (csv/tsv/json/jsonl/tuples/excel + custom); `read()`/`register_reader()`/`get_reader()` | `encino_rpt/readers.py` |
| `evaluate()` | Safe expression evaluator (AST whitelist, no `eval`, anti-DoS limits) | `encino_rpt/expressions.py` |
| `render()` | `{{token}}` template interpolation for header/footer and link/image URLs | `encino_rpt/template.py` |
| `build()` | Orchestrates `run()`: validate, visible columns, row enrichment, group tree, totals, deferred `TOTAL(...)` resolution, template rendering, KPIs → `ReportResult` | `encino_rpt/aggregation.py` |
| `build_chart()` | Derives `Chart.labels`/`series` from already-aggregated child groups or the group's own totals | `encino_rpt/charts.py` |
| `build_pivot()` | Builds a rows × columns cross-tab matrix (`Pivot`) with row/column totals | `encino_rpt/pivot.py` |
| Canonical models | Serializable tree as **stdlib dataclasses**: `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta` | `encino_rpt/models.py` |
| `to_jsonable()`/`from_dict()` | JSON-native (de)serialization of the dataclass tree without pydantic | `encino_rpt/_serialize.py` |
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

**Overall:** Layered — a **fluent builder** (`Report`/`Section`) records intent into internal `*Spec` dataclasses; an **in-memory aggregation engine** (`build()`) maps those specs to a **canonical stdlib `@dataclass` tree**; a **visitor-style renderer layer** walks that tree through a shared generator.

**Key Characteristics:**
- **Fluent builder** returning `self` (or `Section`) for chaining; validation raises early (`encino_rpt/report.py`, `encino_rpt/section.py`).
- **Spec decoupling**: `*Spec` dataclasses (`encino_rpt/_specs.py`) record what the user declared; `build()` maps them to canonical `models.py` types that never appear in the builder.
- **Canonical tree is stdlib `@dataclass`** (NOT pydantic). The recursive `Group.children` union (`list[Detail | Group | Chart | Pivot]`) is resolved at deserialization time by a `type` discriminator dispatch map (`_NODES` in `encino_rpt/_serialize.py:22-27`).
- **Three-phase aggregation**: base totals computed per group (phase A), deferred expressions using `TOTAL("seccion.nombre")` resolved after the registry is complete (phase B, `encino_rpt/aggregation.py:494-507`), then `order_by`/`top(n)`/`suppress_zero` applied (phase C, `encino_rpt/aggregation.py:373-401`) before charts/pivots are appended.
- **Shared iterative `walk()` generator** centralizes the visitor traversal that every renderer consumes (`encino_rpt/renderers/_walk.py`).
- **Streaming renderers**: each renderer exposes `render()` (materialized) + `iter_*` (generator) + `write(result, file)`; `ReportResult` mirrors this with `to_*`/`render_*` (and `file=` params) plus `iter_*` convenience methods (`encino_rpt/models.py:224-439`).
- **Lazy imports** for all optional renderer dependencies (`openpyxl`, `reportlab`) and for the engine (`aggregation`) / renderers / readers to break import cycles.
- **In-memory aggregation engine**; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).
- **Module-level dispatch dicts** (`_BINOPS`, `_CMP`, `_OPS`, `_COLOR_OPS`, `_FORMAT_BY_EXT`) instead of if/else chains.

## Layers

### Declarative Layer
- Purpose: Declarative configuration of a report plus multi-format input.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`, `encino_rpt/readers.py`.
- Contains: The `Report` builder, the `Section` facade, internal `*Spec` dataclasses, and the `Reader` protocol + registry.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints), and lazily on `encino_rpt/readers.py` (inside `Report.read`) and `encino_rpt/aggregation.py` (inside `Report.run`).
- Used by: application code (see `README.md` examples).

### Engine Layer
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (helpers `encino_rpt/expressions.py`, `encino_rpt/template.py`, `encino_rpt/charts.py`, `encino_rpt/pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, `_partition`, `_build_group_tree`, `_build_group`, `_build_instance`, `_build_path_group`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_render_templates`, `_build_kpis`.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:426-434`).

### Model Layer
- Purpose: Typed, JSON-serializable representation of the report result.
- Location: `encino_rpt/models.py` (13 dataclasses) + `encino_rpt/_serialize.py`.
- Depends on: stdlib only (`dataclasses`, `typing`, `datetime`, `decimal`, `enum`).
- Used by: the engine (writes), the renderers (read), and downstream consumers (`to_dict()` / `from_dict()` / `to_json()` / `from_json()`).

### Renderer Layer
- Purpose: Convert the canonical tree to a concrete output format.
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `markdown.py`, `_walk.py`, `_format.py`, `_sanitize.py`).
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras).
- Used by: `ReportResult` convenience methods and end users.

## Data Flow

### Primary Request Path (build a report)

1. User instantiates `Report(rows, params, title)` and chains builder calls (`group()`, `detail()`, `add_field()`, `total()`, etc.), which only record `*Spec` objects — no computation yet (`encino_rpt/report.py:19-424`).
2. `Report.run()` lazily imports and delegates to `aggregation.build(self)` (`encino_rpt/report.py:426-434`).
3. `build()` validates sources/parents/custom aggregates (`_validate`, `encino_rpt/aggregation.py:564-583`), computes the visible-column order (`_visible_columns`, `aggregation.py:553-561`), and enriches each row (computed fields, cumulative sums, links, images) via `_enrich` (`aggregation.py:134-163`).
4. The group hierarchy is assembled: `_build_group_tree` resolves the root and parent→child map (`aggregation.py:167-186`), then `_build_group` partitions rows (`_partition`, `aggregation.py:189-212`) and `_build_instance` constructs each `Group` with `Detail`/subgroup children, computing base totals and registering named totals (`aggregation.py:334-403`). Path-based groups (`path="1.2.3"`) go through an iterative trie (`_make_path_node`, `aggregation.py:283-331`).
5. Deferred totals using `TOTAL("seccion.nombre")` are resolved in phase B (`_resolve_deferred`, `aggregation.py:494-507`), and header/footer templates are rendered with the accumulated context (`_render_templates`, `aggregation.py:511-529`).
6. `build()` returns a `ReportResult` with `root`, `meta`, `columns`, `formats`, `styles`, `kpis` (`aggregation.py:614-621`).

### Secondary Flow (read → report)

1. `Report.read(source, format, coerce, columns, **opts)` lazily imports and calls `readers.read()` (`encino_rpt/report.py:75-78`).
2. `read()` resolves the reader name via `_resolve_format` (explicit `format=` or file extension through `_FORMAT_BY_EXT`, `encino_rpt/readers.py:318-347`) and dispatches through `get_reader()` to the registered reader's `read()` (`encino_rpt/readers.py:350-371`).
3. The reader returns `list[dict]`, which `Report.read` passes to `Report(rows=...)` — the builder is then used identically to the direct path.

### Render Flow

1. `ReportResult.to_html()`, `to_csv()`, `to_text()`, `to_markdown()`, `to_json()`, `to_excel()`, `to_pdf()` (or `iter_*`) lazily import the matching renderer (`encino_rpt/models.py:224-439`).
2. The renderer instantiates and calls `render(result)` (or `write(result, file)` / `iter_*(result)`).
3. Most renderers iterate `walk(result.root)` (`encino_rpt/renderers/_walk.py:8-31`), emitting output on `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` events in document order.

**State Management:**
- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:29-42`); no module-level mutable state except the reader registry (`_READERS` in `encino_rpt/readers.py:35`).
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`encino_rpt/aggregation.py:591-604`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl`, set as plain instance attrs in `Group.__post_init__` (`encino_rpt/models.py:153-159`), replicating the former pydantic `PrivateAttr`.
- A fresh `Report` instance is required per report — `run()` does not reset the builder.

## Key Abstractions

### `ReportResult` (canonical contract)
- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:170-439`.
- Pattern: stdlib `@dataclass` with `root: Group` plus `meta`, `columns`, `formats`, `styles`, `kpis`; convenience render methods with lazy imports; `to_dict`/`from_dict`/`from_json` for round-trip.
- Serialization: `to_dict()` → `to_jsonable(self)`; `from_dict(data)` → `_build(ReportResult, data)` (round-trip verified in `tests/test_report.py`).

### `GroupSpec` + `Section` (builder spec + facade)
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:76-93`, `encino_rpt/section.py:8-210`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`encino_rpt/report.py:360-424`).

### Expression evaluator (`evaluate`)
- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:55-123`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `encino_rpt/expressions.py:67-123`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`encino_rpt/expressions.py:46-48`).

### `walk()` (shared traversal)
- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py:8-31`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)` + `iter_*`/`write(result, file)`; register it in `encino_rpt/renderers/__init__.py`.

### `Reader` protocol + registry
- Purpose: Multi-format input to `list[dict]`, decoupled from `Report`.
- Location: `encino_rpt/readers.py`.
- Pattern: `Reader` is a `typing.Protocol` with `read(source, **opts) -> list[dict]`; `register_reader(name, reader)` mutates the module-level `_READERS` dict; `read()` resolves the name via `_resolve_format` (explicit `format=` or file extension) and dispatches through `get_reader()`. Six built-in readers are registered at import (`encino_rpt/readers.py:375-380`).
- Extension: `Report.register_reader(name, reader)` (`encino_rpt/report.py:80-90`) delegates here; custom readers are any object with a `read(source, **opts)` method.

### Path trie (`_PathNode`)
- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:270-331` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

### Public package API
- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, Reader, ...`.
- Responsibilities: re-export the builder, canonical model types, and `Reader` protocol; `__all__` lists 15 public names (`encino_rpt/__init__.py:21-37`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).

### `Report.run()`
- Location: `encino_rpt/report.py:426-434`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.

### `Report.read()` / `Report.register_reader()`
- Location: `encino_rpt/report.py:44-90`.
- Triggers: user call to build a `Report` from a file/file-like/raw source, or to register a custom reader.
- Responsibilities: delegate to `encino_rpt/readers.py`.

### `ReportResult` render methods
- Location: `encino_rpt/models.py:224-439` (`render_html`, `to_csv`, `to_text`, `to_markdown`, `to_excel`, `to_json`, `to_pdf`, plus `iter_html`/`iter_csv`/`iter_text`/`iter_markdown`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

### `readers.read()`
- Location: `encino_rpt/readers.py:350-371`.
- Triggers: `Report.read()` or direct `from encino_rpt.readers import read`.
- Responsibilities: resolve the reader name and dispatch to the reader's `read()`.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async. The reader registry `_READERS` (`encino_rpt/readers.py:35`) is the only module-level mutable state, and it is write-once-at-import plus user `register_reader` calls.
- **Global state:** `ExcelRenderer` stores transient mutable state on `self` (`_ws`, `_result`, `_formulas`, `_row` — `encino_rpt/renderers/excel.py:51-54`), making it non-reentrant across concurrent renders of the same instance. `PdfRenderer` sets `self._normal` during `render` (`encino_rpt/renderers/pdf.py:51`).
- **Circular imports:** Avoided via lazy imports. `report.py` imports `aggregation.py` lazily inside `run()` (`encino_rpt/report.py:432`) and `readers.py` lazily inside `read()`/`register_reader()` (`encino_rpt/report.py:75,88`); `models.py` imports renderers lazily inside convenience methods (`encino_rpt/models.py:224-437`) and `_serialize` lazily inside `to_dict`/`from_dict`. `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`encino_rpt/expressions.py`). `ast.parse` node/depth/pow counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:40-46`) and `ExcelReader.read` (`encino_rpt/readers.py:295-300`); `reportlab` only inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:35-48`). All raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **No pydantic at runtime:** The model layer is stdlib `@dataclass`; serialization is hand-rolled in `encino_rpt/_serialize.py`. The recursive `Group.children` union is deserialized via the `_NODES` discriminator map keyed on each node's `type` field (`encino_rpt/_serialize.py:22-27`).
- **Security posture:** OWASP formula-injection sanitization on CSV/Excel cells (`encino_rpt/renderers/_sanitize.py`); HTML attribute/value whitelisting against CSS injection (`encino_rpt/renderers/html.py:22-23`).

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

**What happens:** `build()` and its helpers reach directly into `Report`'s underscore-prefixed instance attributes across the module boundary — `report._rows`, `report._datasets`, `report._fields`, `report._functions`, `report._aggregates`, `report._detail`, `report._detail_source`, `report._groups`, `report._order`, `report._formats`, `report._styles`, `report._kpis`, `report._title`, `report._params` (see `_enrich` at `encino_rpt/aggregation.py:134-163`, `_build_group_tree` at `167-186`, and `build` at `586-621`).

**Why it's wrong:** The engine depends on the exact private attribute names and layout of `Report`. Renaming or restructuring builder state silently breaks aggregation, and the coupling is only caught at runtime (there is no shared interface between the two modules).

**Do this instead:** Pass an explicit, typed snapshot (e.g. a `BuildContext` dataclass) from `Report.run()` into `build()`, so the engine reads declared public state rather than poking private fields. Alternatively, expose read-only properties on `Report` and have `aggregation.py` consume those.

### Charts/pivots appended after phase-C ordering

**What happens:** In `_build_instance`, `_apply_order` (order/top/suppress_zero) runs only over `node.children` (groups/detail), and then `extras` (charts/pivots) are concatenated afterwards (`encino_rpt/aggregation.py:373-401`).

**Why it's wrong:** `top(n)` and `suppress_zero` never filter charts/pivots, and ordering never places them relative to children — they always render last, regardless of `order_by`. Callers expecting a chart to respect `top()` or appear inline are surprised.

**Do this instead:** Model charts/pivots as ordered children with an explicit position field, and apply phase-C transforms to the full child list (including extras), or document and enforce the "extras always last" invariant with validation.

### Duplicated operator/conditional tables per renderer

**What happens:** The comparison operator dispatch (`lt/le/gt/ge/eq/ne`) is re-declared as module-level lambda dicts in both `encino_rpt/renderers/html.py:13-20` (`_OPS`) and `encino_rpt/renderers/excel.py:10-17` (`_COLOR_OPS`), duplicating the semantics already encoded in `expressions._CMP` (`encino_rpt/expressions.py:22-29`).

**Why it's wrong:** Three copies of the same six comparisons can drift (e.g. a future `between`/`in` operator added to one renderer but not the other), producing inconsistent conditional formatting between HTML and Excel.

**Do this instead:** Extract a single shared comparison module (e.g. `encino_rpt/renderers/_cond.py`) that maps operator name → comparison callable, and import it from both renderers.

### Per-renderer event-handling duplication around `walk()`

**What happens:** Although traversal is centralized in `walk()`, each renderer re-implements the same `(event, node)` dispatch switch with its own local state: `_walk_chunks`/`depth` in `html.py:101-151` and `text.py:58-94`, `_walk_rows` in `csv.py:76-116`, `_walk_lines`+`pending` in `markdown.py:112-148`, `_walk`+`group_stack` in `excel.py:73-127`, `_collect`+`spans` in `pdf.py:94-128`.

**Why it's wrong:** The label-fallback logic (`t.label or t.name or t.operator`), format resolution (`t.format or result.formats.get(t.column)`), and group-depth bookkeeping are copy-pasted six times. A change to how totals are labeled or formatted must be applied in every renderer.

**Do this instead:** Provide a higher-level "row emitter" helper in the renderer package that resolves labels/formats once and calls per-event hooks, so renderers only implement output specifics.

## Error Handling

**Strategy:** Fail fast and loudly with typed, Spanish-language exceptions carrying the offending name/value via `{x!r}`. No logging framework — errors surface as exceptions.

**Patterns:**
- **Builder validation:** `group()` raises `ValueError` when `columns` and `path` are both set (`encino_rpt/report.py:388-389`) and on duplicate cut names (`report.py:390-391`); `section()` raises `KeyError` for undeclared cuts (`report.py:421-423`); `Section.order_by` raises `ValueError` for invalid direction (`encino_rpt/section.py:163-164`).
- **Reader errors:** `get_reader()` raises `ValueError` for unregistered readers (`encino_rpt/readers.py:60-63`); `read()` raises `ValueError` when the format can't be resolved (`readers.py:347`); `TuplesReader` raises `ValueError` when `columns` is missing or mismatched (`readers.py:264-273`); JSON/JSONL readers raise `TypeError` for non-list/non-dict payloads.
- **Engine context wrapping:** `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:35-44`).
- **Expression errors:** `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`encino_rpt/expressions.py:51-123`).
- **Template errors:** `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`encino_rpt/template.py:20-32`).
- **Aggregate errors:** `ValueError` for unknown operators (`encino_rpt/aggregation.py:69`); `AggregationError` for unregistered custom aggregates (`aggregation.py:87`, `575`).
- **Optional dependency errors:** `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:43-46`, `renderers/pdf.py:45-48`, `readers.py:297-300`) — covered by `pytest.importorskip` in tests.
- **Serialization errors:** `JsonRenderer.render`/`to_dict` and `from_dict` convert deep-recursion `RecursionError` into a controlled `ValueError` (`renderers/json.py:29-41`, `_serialize.py:43-46`, `_serialize.py:126-129`).
- **Aggregation never catches exceptions:** a failing expression propagates up through `run()` to the caller.

## Cross-Cutting Concerns

**Logging:** No logging framework — the library is pure and side-effect-free; all diagnostics are exceptions (`encino_rpt/`).

**Validation:** Two distinct layers — builder-time validation (`Report`/`Section`/`Reader` raise on bad config) and engine-time validation (`_validate` checks source/parent/custom-aggregate references, `encino_rpt/aggregation.py:564-583`); the model dataclasses also validate enums in `__post_init__` (e.g. `Format.kind`, `Link.target`, `Chart.kind`, `ConditionalRule.when` in `encino_rpt/models.py`).

**Authentication:** Not applicable — a library with no network/identity surface.

**Security:** Expression evaluation uses AST whitelist (no `eval`) with DoS caps (`encino_rpt/expressions.py`); CSV/Excel output sanitizes OWASP formula injection (`encino_rpt/renderers/_sanitize.py`); HTML escapes all dynamic content and whitelists CSS property names/values (`encino_rpt/renderers/html.py:22-23`, `_style_items` at `218-235`).

---

*Architecture analysis: 2026-09-17*
