<!-- refreshed: 2026-09-17 -->
# Architecture

**Analysis Date:** 2026-09-17

## System Overview

`encino-rpt` is a financial report generator (a **library**, not a server) that consumes an already-materialized `list[dict]` and produces a canonical serializable tree (`ReportResult`) with optional renderers to HTML, Excel, CSV, PDF, Markdown, JSON and plain text. Aggregation and rendering must be exact, idempotent and injection-safe.

```text
┌───────────────────────────────────────────────────────────────────────┐
│                        Builder / Config layer                         │
│  Report (fluent)   Section (facade)   *Spec dataclasses   Reader proto │
│  `encino_rpt/report.py`  `encino_rpt/section.py`  `encino_rpt/_specs.py`│
│                                     `encino_rpt/readers.py`            │
└──────────────────────────────┬────────────────────────────────────────┘
                               │  Report.run() → build(self)
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          Engine layer                                  │
│  aggregation.build() + expressions / template / charts / pivot helpers │
│  `encino_rpt/aggregation.py`  `encino_rpt/expressions.py`              │
│  `encino_rpt/template.py`  `encino_rpt/charts.py`  `encino_rpt/pivot.py`│
└──────────────────────────────┬────────────────────────────────────────┘
                               │  ReportResult (canonical tree)
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    Canonical model layer (stdlib dataclasses)          │
│  `encino_rpt/models.py`  +  `encino_rpt/_serialize.py` (JSON round-trip)│
└──────────────────────────────┬────────────────────────────────────────┘
                               │  ReportResult.to_* / render_* / iter_*
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│                        Renderer layer (visitors)                       │
│  `encino_rpt/renderers/_walk.py` (shared traversal)                    │
│  Html / Excel / Csv / Text / Markdown / Pdf / Json renderers           │
│  + `_format.py` (value formatting) + `_sanitize.py` (OWASP)            │
└───────────────────────────────────────────────────────────────────────┘
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

- **Fluent builder** returning `self` (or `Section`) for chaining; validation raises early (`report.py`, `section.py`).
- **Spec decoupling**: `*Spec` dataclasses (`_specs.py`) record what the user declared; `build()` maps them to canonical `models.py` types that never appear in the builder.
- **Canonical tree is stdlib `@dataclass`** (NOT pydantic). The recursive `Group.children` union (`list[Detail | Group | Chart | Pivot]`) is resolved at deserialization time by a `type` discriminator dispatch map (`_NODES` in `encino_rpt/_serialize.py:17-22`).
- **Two-phase total resolution**: base totals computed per group first, then deferred expressions using `TOTAL("seccion.nombre")` resolved in phase B (`encino_rpt/aggregation.py:494-507`).
- **Post-processing phase C**: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed, before charts/pivots are appended (`encino_rpt/aggregation.py:373-401`).
- **Shared iterative `walk()` generator** centralizes the visitor traversal that every renderer consumes (`encino_rpt/renderers/_walk.py`).
- **Streaming renderers**: each renderer exposes `render()` (materialized) + `iter_*` (generator) + `write(result, file)`; `ReportResult` mirrors this with `to_*`/`render_*` (and `file=` params) plus `iter_*` convenience methods (`encino_rpt/models.py:204-419`).
- **Lazy imports** for all optional renderer dependencies (`openpyxl`, `reportlab`) and for the engine (`aggregation`) / renderers / readers to break import cycles.
- **In-memory aggregation engine**; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).
- **Module-level dispatch dicts** (`_BINOPS`, `_CMP`, `_OPS`, `_COLOR_OPS`, `_FORMAT_BY_EXT`) instead of if/else chains.

## Layers

**Builder / Config:**
- Purpose: Declarative configuration of a report plus multi-format input.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`, `encino_rpt/readers.py`.
- Contains: The `Report` builder, the `Section` facade, internal `*Spec` dataclasses, and the `Reader` protocol + registry.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints), and lazily on `encino_rpt/readers.py` (inside `Report.read`) and `encino_rpt/aggregation.py` (inside `Report.run`).
- Used by: application code (see `README.md` examples).

**Engine:**
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, `_partition`, `_build_group_tree`, `_build_group`, `_build_instance`, `_build_path_group`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_render_templates`, `_build_kpis`.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:426-434`).

**Canonical model + serialization:**
- Purpose: Typed, JSON-serializable representation of the report result.
- Location: `encino_rpt/models.py` (13 dataclasses) + `encino_rpt/_serialize.py`.
- Depends on: stdlib only (`dataclasses`, `typing`, `datetime`, `decimal`, `enum`).
- Used by: the engine (writes), the renderers (read), and downstream consumers (`to_dict()` / `from_dict()` / `to_json()` / `from_json()`).

**Renderer:**
- Purpose: Convert the canonical tree to a concrete output format.
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `markdown.py`, `_walk.py`, `_format.py`, `_sanitize.py`).
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras).
- Used by: `ReportResult` convenience methods and end users.

## Data Flow

### Primary Request Path (build a report)

1. `Report(rows, params, title)` stores config in private instance attrs (`encino_rpt/report.py:19-42`).
2. Builder methods mutate `self._fields` / `self._groups` / `self._styles` / etc., each returning `self` or a `Section`.
3. `Report.run()` (`encino_rpt/report.py:426`) lazily imports and calls `aggregation.build(self)`.
4. `build()` validates (`_validate`), computes visible columns (`_visible_columns`), and enriches every source dataset (`_enrich` → `evaluate`/template for `expr`/`link`/`image` fields) — `encino_rpt/aggregation.py:586-593`.
5. `_build_group_tree` resolves the root spec + parent→children map; `_build_group` partitions rows (`_partition`) and recursively builds `Group`/`Detail` nodes, computing base totals and registering deferred `TOTAL(...)` totals (`aggregation.py:215-403`).
6. `_resolve_deferred` resolves phase-B totals with a `TOTAL` function bound to the cross-group registry (`aggregation.py:494-507`).
7. `_render_templates` walks the tree and renders header/footer templates with the final total context (`aggregation.py:511-529`).
8. `build()` returns a `ReportResult` with `meta`, `columns`, `formats`, `styles`, `kpis`, `root` (`aggregation.py:614-621`).

### Secondary Flow (read → report)

1. `Report.read(source, format, coerce, columns, ...)` (`encino_rpt/report.py:44-78`) delegates to `readers.read`.
2. `readers.read` resolves the reader via `_resolve_format` (explicit `format=` or file extension) and dispatches through `get_reader` (`encino_rpt/readers.py:350-371`).
3. The reader returns `list[dict]`, which `Report.read` passes to `cls(rows, ...)`.

### Render Flow

1. End user calls `result.to_html()` / `to_csv()` / `iter_html()` / etc. (`encino_rpt/models.py`).
2. The method lazy-imports the matching renderer and delegates to `render()` (string) or `write(result, file)` (streaming), or `iter_*` (generator).
3. Each renderer consumes `walk(result.root)` (`encino_rpt/renderers/_walk.py`) and emits its format.

**State Management:**
- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:29-42`); no module-level mutable state except the reader registry (`_READERS` in `encino_rpt/readers.py:35`).
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:603-604`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl`, set as plain instance attrs in `Group.__post_init__` (`encino_rpt/models.py:133-138`), replicating the former pydantic `PrivateAttr`.
- A fresh `Report` instance is required per report — `run()` does not reset the builder.

## Key Abstractions

**`ReportResult` (canonical tree):**
- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:149-419`.
- Pattern: stdlib `@dataclass` with `root: Group` plus `meta`, `columns`, `formats`, `styles`, `kpis`; convenience render methods with lazy imports; `to_dict`/`from_dict`/`from_json` for round-trip.
- Serialization: `to_dict()` → `to_jsonable(self)`; `from_dict(data)` → `_build(ReportResult, data)` (round-trip verified in `tests/test_report.py`).

**`GroupSpec` + `Section`:**
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:75-93`, `encino_rpt/section.py`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`encino_rpt/report.py:360-424`).

**Expression evaluator:**
- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:55-123`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:67-123`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:46-48`).

**Tree walker:**
- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)` + `iter_*`/`write(result, file)`; register it in `encino_rpt/renderers/__init__.py`.

**Readers + registry:**
- Purpose: Multi-format input to `list[dict]`, decoupled from `Report`.
- Location: `encino_rpt/readers.py`.
- Pattern: `Reader` is a `typing.Protocol` with `read(source, **opts) -> list[dict]`; `register_reader(name, reader)` mutates the module-level `_READERS` dict; `read()` resolves the name via `_resolve_format` (explicit `format=` or file extension) and dispatches through `get_reader()`. Six built-in readers are registered at import (`readers.py:375-380`).
- Extension: `Report.register_reader(name, reader)` (`encino_rpt/report.py:80-90`) delegates here; custom readers are any object with a `read(source, **opts)` method.

**Path hierarchy (trie):**
- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:270-331` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

**Package import:**
- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, Reader, ...`.
- Responsibilities: re-export the builder, canonical model types, and `Reader` protocol; `__all__` lists 15 public names (`__init__.py:21-37`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).

**`Report.run()`:**
- Location: `encino_rpt/report.py:426-434`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.

**`Report.read()` / `register_reader()`:**
- Location: `encino_rpt/report.py:44-90`.
- Triggers: user call to build a `Report` from a file/file-like/raw source, or to register a custom reader.
- Responsibilities: delegate to `encino_rpt/readers.py`.

**`ReportResult` convenience methods:**
- Location: `encino_rpt/models.py:150-419` (`render_html`, `to_csv`, `to_text`, `to_markdown`, `to_excel`, `to_json`, `to_pdf`, plus `iter_html`/`iter_csv`/`iter_text`/`iter_markdown`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

**`readers.read()`:**
- Location: `encino_rpt/readers.py:350-371`.
- Triggers: `Report.read()` or direct `from encino_rpt.readers import read`.
- Responsibilities: resolve the reader name and dispatch to the reader's `read()`.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async. The reader registry `_READERS` (`encino_rpt/readers.py:35`) is the only module-level mutable state, and it is write-once-at-import plus user `register_reader` calls.
- **Global state:** `ExcelRenderer` stores transient mutable state on `self` (`_ws`, `_result`, `_formulas`, `_row` — `encino_rpt/renderers/excel.py:51-54`), making it non-reentrant across concurrent renders of the same instance. `PdfRenderer` sets `self._normal` during `render` (`encino_rpt/renderers/pdf.py:51`).
- **Circular imports:** Avoided via lazy imports. `report.py` imports `aggregation.py` lazily inside `run()` (`report.py:432`) and `readers.py` lazily inside `read()`/`register_reader()` (`report.py:75,88`); `models.py` imports renderers lazily inside convenience methods (`models.py:232-417`) and `_serialize` lazily inside `to_dict`/`from_dict`. `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`encino_rpt/expressions.py`). `ast.parse` node/depth/pow counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`encino_rpt/renderers/excel.py:40-46`) and `ExcelReader.read` (`encino_rpt/readers.py:295-300`); `reportlab` only inside `PdfRenderer.render` (`encino_rpt/renderers/pdf.py:35-48`). All raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **No pydantic at runtime:** The model layer is stdlib `@dataclass`; serialization is hand-rolled in `encino_rpt/_serialize.py`. The recursive `Group.children` union is deserialized via the `_NODES` discriminator map keyed on each node's `type` field (`_serialize.py:17-22`).

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

**What happens:** The engine reads `report._rows`, `report._fields`, `report._groups`, `report._datasets`, `report._functions`, `report._aggregates`, `report._kpis`, `report._detail`, `report._detail_source`, `report._order` directly (`encino_rpt/aggregation.py:134-621`), rather than going through `Report` accessors.
**Why it's wrong:** Any rename of a private `Report` attribute silently breaks the engine; there is no interface contract beyond "both files know the same names."
**Do this instead:** Keep the spec dataclasses as the boundary — if you add builder state, add a corresponding `*Spec` field (or a typed accessor on `Report`) and read it through `_specs.py` rather than reaching into `report._*`.

### Charts/pivots appended after phase-C ordering

**What happens:** `_apply_order` (order/top/suppress_zero) runs on `node.children` **before** charts/pivots are appended (`encino_rpt/aggregation.py:373-401`).
**Why it's wrong:** Charts/pivots can never be reordered or filtered by `order_by`/`top`/`suppress_zero`; they are always last. This is intentional but surprising if you assume ordering applies to all children.
**Do this instead:** Preserve this invariant — charts/pivots are always emitted after ordered child groups. Document that ordering only affects `Group`/`Detail` children.

### Duplicated operator/conditional tables per renderer

**What happens:** `_OPS` (`encino_rpt/renderers/html.py:13-20`), `_COLOR_OPS` (`encino_rpt/renderers/excel.py:10-17`) and the expression `_CMP` (`encino_rpt/expressions.py:22-29`) each re-implement the same `lt/le/gt/ge/eq/ne` comparison semantics.
**Why it's wrong:** Adding a comparison operator means editing three files; drift between them introduces inconsistent conditional styling.
**Do this instead:** Prefer a single shared comparison helper (e.g. in a small shared module) when touching conditional styling; at minimum, keep the three tables in sync.

### Reimplementing tree traversal per renderer

**What happens:** Some renderers maintain their own `depth`/`pending` state on top of `walk()` (e.g. `MarkdownRenderer._walk_lines` — `markdown.py:112-148`), while `walk()` already yields the events.
**Why it's wrong:** Custom state machines per renderer are error-prone and duplicate what `walk()` provides.
**Do this instead:** Consume `walk()` events directly; introduce renderer-local state only when the format truly needs buffering (as Markdown does to batch detail rows into one table).

## Error Handling

- **Builder validation:** `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:388-389`) and on duplicate cut names (`report.py:390-391`); `section()` raises `KeyError` for undeclared cuts (`report.py:421-423`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:163-164`).
- **Reader errors:** `get_reader()` raises `ValueError` for unregistered readers (`readers.py:60-63`); `read()` raises `ValueError` when the format can't be resolved (`readers.py:347`); `TuplesReader` raises `ValueError` when `columns` is missing or mismatched (`readers.py:264-273`); JSON/JSONL readers raise `TypeError` for non-list/non-dict payloads.
- **Engine context wrapping:** `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`encino_rpt/aggregation.py:35-44`).
- **Expression errors:** `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`encino_rpt/expressions.py:51-123`).
- **Template errors:** `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`encino_rpt/template.py:20-31`).
- **Aggregate errors:** `ValueError` for unknown operators (`aggregation.py:69`); `AggregationError` for unregistered custom aggregates (`aggregation.py:87`, `575`).
- **Optional dependency errors:** `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:43-46`, `renderers/pdf.py:45-48`, `readers.py:297-300`) — covered by `pytest.importorskip` in tests.
- **Serialization errors:** `JsonRenderer.render`/`to_dict` convert deep-recursion `RecursionError` into a controlled `ValueError` (`renderers/json.py:34-51`).
- **Aggregation never catches exceptions:** a failing expression propagates up through `run()` to the caller.

## Cross-Cutting Concerns

**Logging:** None. The library uses no logging framework — errors propagate as exceptions; there is no `logging` import anywhere in `encino_rpt/`.

**Validation:** Split between the builder (early, fluent `ValueError`/`KeyError`) and the engine (`_validate` in `encino_rpt/aggregation.py:564-583`, which checks `source`/`parent`/`custom:` references across groups, fields, detail and KPIs before aggregation).

**Authentication:** None. The library is pure and stateless; no network, auth, or secrets handling.

**Security:** Two dedicated subsystems — the AST-whitelist expression evaluator (`encino_rpt/expressions.py`) and OWASP formula-injection mitigation (`encino_rpt/renderers/_sanitize.py`, applied in CSV via `sanitize_csv` and in Excel via `write_excel_cell`). HTML escaping is applied via `html.escape` in `html.py`/`pdf.py`.

**Serialization:** `encino_rpt/_serialize.py` handles dataclass→JSON-native conversion (`to_jsonable`) and reverse (`from_dict` via `get_type_hints` + `_coerce`), including `Decimal`→str, `datetime`/`date`/`time`→isoformat, `Enum`→value, and recursive-union dispatch via the `type` discriminator.

---

*Architecture analysis: 2026-09-17*
