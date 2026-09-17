<!-- refreshed: 2026-09-17 -->
# Architecture

**Analysis Date:** 2026-09-17

## System Overview

```text
┌───────────────────────────────────────────────────────────────────────┐
│                        CONFIGURACIÓN (Builder)                          │
│  Report (fluent) · Section (facade) · *Spec (dataclasses internos)      │
│  encino_rpt/report.py · encino_rpt/section.py · encino_rpt/_specs.py    │
└───────────────────────────────┬───────────────────────────────────────┘
                                │ Report.run()  →  aggregation.build(self)
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                          MOTOR DE AGREGACIÓN                            │
│  build() · _enrich · _build_group_tree · _partition · _compute_totals   │
│  _apply_order · _resolve_deferred · _render_templates · _build_kpis     │
│  encino_rpt/aggregation.py                                              │
│  + helpers: expressions.py · template.py · charts.py · pivot.py         │
└───────────────────────────────┬───────────────────────────────────────┘
                                │ construye
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    MODELO CANÓNICO (pydantic v2)                        │
│  ReportResult · Group · Detail · Total · Chart · Pivot · Kpi · Format   │
│  Link · Image · ConditionalRule · Series · ReportMeta                    │
│  encino_rpt/models.py  (serializable a JSON vía model_dump)             │
└───────────────────────────────┬───────────────────────────────────────┘
                                │ ReportResult.to_* / render_*
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                         RENDERERS (visitor)                             │
│  walk() compartido  →  Html · Excel · Csv · Text · Pdf · Json           │
│  encino_rpt/renderers/ (+ _walk.py · _format.py · _sanitize.py)         │
└───────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs, custom functions/aggregates; `run()` materializes the tree | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a group's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress_zero/page_break) | `encino_rpt/section.py` |
| `FieldSpec`/`GroupSpec`/`TotalSpec`/`ChartSpec`/`PivotSpec`/`KpiSpec` | Internal builder specifications (dataclasses) — NOT part of the canonical tree | `encino_rpt/_specs.py` |
| `evaluate()` | Safe expression evaluator (AST whitelist, no `eval`, anti-DoS limits) | `encino_rpt/expressions.py` |
| `render()` | `{{token}}` template interpolation for header/footer and link/image URLs | `encino_rpt/template.py` |
| `build()` | Orchestrates `run()`: validate, visible columns, row enrichment, group tree construction, totals, deferred `TOTAL(...)` resolution, template rendering, KPIs → `ReportResult` | `encino_rpt/aggregation.py` |
| `build_chart()` | Derives `Chart.labels`/`series` from already-aggregated child groups or the group's own totals | `encino_rpt/charts.py` |
| `build_pivot()` | Builds a rows × columns cross-tab matrix (`Pivot`) with row/column totals | `encino_rpt/pivot.py` |
| Pydantic models | Canonical serializable tree: `ReportResult`, `Group`, `Detail`, `Chart`, `Pivot`, `Kpi`, `Total`, `Format`, `Link`, `Image`, `ConditionalRule`, `Series`, `ReportMeta` | `encino_rpt/models.py` |
| `walk()` | Shared iterative tree traversal; yields typed `(event, node)` tuples consumed by every renderer | `encino_rpt/renderers/_walk.py` |
| `HtmlRenderer` | Consumes `walk()` → HTML `<table>` with classes, conditional styles, pivot sub-tables | `encino_rpt/renderers/html.py` |
| `ExcelRenderer` | Consumes `walk()` → openpyxl `Worksheet` (optional dep), native charts, `=SUM(...)` formula mode, cell formatting | `encino_rpt/renderers/excel.py` |
| `CsvRenderer` | Consumes `walk()` → flattened CSV with formula-injection sanitization | `encino_rpt/renderers/csv.py` |
| `TextRenderer` | Consumes `walk()` → indented plain text for inspection | `encino_rpt/renderers/text.py` |
| `PdfRenderer` | Consumes `walk()` → reportlab PDF bytes (optional dep), span-based layout | `encino_rpt/renderers/pdf.py` |
| `JsonRenderer` | Serializes `ReportResult` to JSON with `schema_version` (`"1.0"`) | `encino_rpt/renderers/json.py` |
| `format_value`/`excel_number_format` | Shared value formatting per `Format` (currency, %, thousands, parens, dates) | `encino_rpt/renderers/_format.py` |
| `sanitize_csv`/`write_excel_cell`/`is_dangerous` | OWASP formula-injection mitigation for CSV/Excel output | `encino_rpt/renderers/_sanitize.py` |

## Pattern Overview

**Overall:** Layered fluent-builder → aggregation-engine → pydantic-canonical-model → visitor-renderers pipeline.

**Key Characteristics:**
- Fluent builder API returning `self` for chaining (`report.py`, `section.py`); validation raises early (e.g. `group()` duplicate cut `report.py:325-326`).
- Spec objects (`_specs.py`) decouple what the user declared from the canonical output — specs are consumed by `build()` and never appear in the result tree.
- Two-phase total resolution: base totals first, then deferred expressions using `TOTAL("seccion.nombre")` (phase B in `aggregation.py:448-461`).
- Post-processing phase C: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed, before charts/pivots are appended (`aggregation.py:349-368`).
- Pydantic v2 models with typed discriminators (`type: Literal[...]`) for polymorphic children; the recursive `Group.children` union is resolved via `Group.model_rebuild()` (`models.py:232`).
- Shared iterative `walk()` generator centralizes the visitor traversal that each renderer previously duplicated (`renderers/_walk.py`).
- Lazy imports for all optional renderer dependencies (`openpyxl`, `reportlab`) and for the engine (`aggregation`) / renderers to break import cycles.
- In-memory aggregation engine; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).

## Layers

**Configuration (Builder):**
- Purpose: Declarative configuration of a report.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`.
- Contains: The `Report` builder, the `Section` facade, and internal `*Spec` dataclasses.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints).
- Used by: application code (see `README.md` examples).

**Engine:**
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, `_partition`, `_build_group_tree`, `_build_group`, `_build_instance`, `_compute_totals_into`, `_resolve_deferred`, `_apply_order`, `_render_templates`, `_build_kpis`.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:361-369`).

**Canonical Model:**
- Purpose: Typed, JSON-serializable representation of the report result.
- Location: `encino_rpt/models.py`.
- Contains: 13 pydantic models (see Component Responsibilities table).
- Depends on: `pydantic>=2` only.
- Used by: the engine (writes), the renderers (read), and downstream consumers (`model_dump()` / `model_validate()` / `to_json()`).

**Renderers:**
- Purpose: Convert the canonical tree to a concrete output format.
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `_walk.py`, `_format.py`, `_sanitize.py`).
- Contains: Visitor-style renderer classes + shared walker/formatting/sanitizing helpers.
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras).
- Used by: `ReportResult` convenience methods and end users.

## Data Flow

### Primary Request Path (build a report)

1. User constructs `Report(rows, params, title)` and declares fields/groups via fluent methods (`encino_rpt/report.py:19-40`).
2. `Report.run()` lazily imports the engine and delegates: `from .aggregation import build; return build(self)` (`encino_rpt/report.py:361-369`).
3. `build()` validates (`_validate`, `aggregation.py:518-535`) and computes visible columns (`_visible_columns`, `aggregation.py:507-515`).
4. Rows are enriched per source (`_enrich`, `aggregation.py:123-152`) — computed fields via `evaluate`, cumulative sums, links/images via `render_template`.
5. The group hierarchy is derived (`_build_group_tree`, `aggregation.py:156-175`) and instantiated recursively (`_build_group` → `_build_instance`, `aggregation.py:192-370`), partitioning rows by key (`_partition`, `aggregation.py:178-189`) or by path trie (`_make_path_node`, `aggregation.py:259-307`).
6. Base totals are computed and named totals registered in `registry` (`_compute_totals_into`, `aggregation.py:214-235`); deferred `TOTAL(...)` expressions are queued.
7. Phase C ordering/filtering is applied to children (`_apply_order`, `aggregation.py:373-385`), then charts/pivots are appended (`aggregation.py:352-368`).
8. Deferred totals are resolved with `TOTAL` injected as a function (`_resolve_deferred`, `aggregation.py:448-461`).
9. Header/footer templates are rendered in a final pass (`_render_templates`, `aggregation.py:465-483`).
10. `ReportResult` is assembled with meta, columns, formats, styles, KPIs and the root `Group` (`aggregation.py:559-566`).

### Secondary Flow (render to a destination)

1. End user calls a convenience method, e.g. `result.to_csv()` (`encino_rpt/models.py:166-177`).
2. The method lazy-imports the matching renderer and delegates, never mutating the tree (`models.py:175-177`).
3. The renderer iterates the shared `walk(root)` generator (`encino_rpt/renderers/_walk.py:8-31`), which yields typed events (`group_start`, `detail`, `chart`, `pivot`, `group_end`) in document order.
4. Each renderer dispatches per event and applies shared helpers: `format_value`/`excel_number_format` (`_format.py`) and `sanitize_csv`/`write_excel_cell` (`_sanitize.py`).

**State Management:**
- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:29-41`); there is no module-level mutable state.
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:543-549`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl` via pydantic `PrivateAttr` (`encino_rpt/models.py:123-126`).
- A fresh `Report` instance is required per report — `run()` does not reset the builder, so re-running `run()` re-executes the full aggregation.

## Key Abstractions

**`ReportResult` (canonical tree):**
- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:136-228`.
- Pattern: pydantic `BaseModel` with typed children (`root: Group`), convenience render methods with lazy imports, `to_json` with `schema_version`.
- Serialization: `model_dump()` / `model_validate()` round-trip verified in `tests/test_report.py`.

**`GroupSpec` + `Section` (spec/facade):**
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:77-96`, `encino_rpt/section.py`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`report.py:295-359`).

**`evaluate()` (safe expressions):**
- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:55-123`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:67-123`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:46-48`).

**`walk()` (shared traversal):**
- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)`; register it in `encino_rpt/renderers/__init__.py`.

**Path trie (`_PathNode`):**
- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:246-307` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

**Package re-exports:**
- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, ...`.
- Responsibilities: re-export the builder and canonical model types; `__all__` lists 14 public names (`__init__.py:20-34`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).

**`Report.run()`:**
- Location: `encino_rpt/report.py:361-369`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.

**`ReportResult` convenience methods:**
- Location: `encino_rpt/models.py:150-229` (`render_html`, `to_csv`, `to_text`, `to_excel`, `to_json`, `to_pdf`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async, no shared state outside the `Report` instance. Engine helpers in `aggregation.py` are module-level functions with private `_`-prefixed names.
- **Global state:** None at module level. All mutable state is per-`Report` instance or local to `build()`. The `ExcelRenderer` stores transient mutable state on `self` (`_ws`, `_result`, `_formulas`, `_row` — `renderers/excel.py:55-58`), making it non-reentrant across concurrent renders of the same instance.
- **Circular imports:** Avoided. `report.py` imports `aggregation.py` lazily inside `run()` (`report.py:367`); `models.py` imports renderers lazily inside convenience methods (`models.py:162-227`). `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`expressions.py`). `ast.parse` node/depth counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`renderers/excel.py:44-46`); `reportlab` only inside `PdfRenderer.render` (`renderers/pdf.py:31-41`). Both raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **Pydantic forward references:** `Group.children` is a recursive union, resolved with `Group.model_rebuild()` at the bottom of `encino_rpt/models.py:232`.

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

**What happens:** `build()` and its helpers reach directly into `Report` internals — `report._rows`, `report._datasets`, `report._fields`, `report._functions`, `report._aggregates`, `report._groups`, `report._order`, `report._formats`, `report._styles`, `report._kpis`, `report._title`, `report._params` (e.g. `aggregation.py:124`, `157-175`, `529-535`, `562-564`).
**Why it's wrong:** The engine depends on builder internals rather than a stable, frozen spec snapshot. Renaming or restructuring a private `Report` attribute silently breaks the engine with no static signal.
**Do this instead:** Have `Report.run()` pass a frozen, read-only context object (or expose typed read-only accessors) so the engine depends on a public contract, not private attribute names.

### Charts/pivots appended after phase-C ordering

**What happens:** `_build_instance` applies `order_by`/`top`/`suppress_zero` to children (`node.children = _apply_order(...)`, `aggregation.py:350`), then appends charts and pivots afterward (`node.children = node.children + extras`, `aggregation.py:368`).
**Why it's wrong:** Charts/pivots bypass ordering/top/suppression, so `child_pairs` (used to build charts, `aggregation.py:358`) reflects the pre-order child set while their final position in `children` is post-order — inconsistent ordering semantics and a foot-gun for consumers expecting `children` to be fully ordered.
**Do this instead:** Build charts/pivots from the already-ordered children list, or explicitly document that charts/pivots are always appended last and excluded from ordering.

### Duplicated operator/conditional tables per renderer

**What happens:** `_OPS` (`renderers/html.py:12-19`) and `_COLOR_OPS` (`renderers/excel.py:10-17`) duplicate the same six comparison lambdas (`lt/le/gt/ge/eq/ne`); the `label or name or operator` fallback is repeated in `csv.py:55`, `text.py:46`, `html.py:71`, `pdf.py:96`, `excel.py:107`.
**Why it's wrong:** Adding a new conditional operator (or changing fallback semantics) requires editing every renderer, risking drift between formats.
**Do this instead:** Extract a single shared comparison/fallback helper module (e.g. next to `_format.py`) and import it from both renderers.

### Reimplementing tree traversal per renderer

**What happens:** Every renderer defines its own private `_walk(self, root, ...)` method that consumes the shared `walk()` generator and re-dispatches the same five events (`csv.py:48-95`, `text.py:35-72`, `html.py:53-110`, `excel.py:77-131`, `pdf.py:88-122`).
**Why it's wrong:** The event dispatch skeleton is duplicated, so a new node type or event added to `_walk.py` requires touching all five renderers (historically this is why `_walk.py` was introduced, but per-renderer dispatch remains duplicated).
**Do this instead:** Consider a small shared `visit(root, handlers: dict[str, callable])` helper that invokes registered callbacks, leaving renderers to supply only the handlers.

## Error Handling

**Strategy:** Fail fast and loud — validation raises immediately in the builder, and the engine wraps failures with human-readable context (`AggregationError`). The library never catches-and-swallows; it propagates to the caller.

**Patterns:**
- Builder validation: `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:323-324`) and on duplicate cut names (`report.py:325-326`); `section()` raises `KeyError` for undeclared cuts (`report.py:356-358`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:172-173`).
- Engine context wrapping: `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`aggregation.py:34-43`).
- Expression errors: `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`expressions.py:51-123`).
- Template errors: `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`template.py:20-31`).
- Aggregate errors: `ValueError` for unknown operators (`aggregation.py:68`); `AggregationError` for unregistered custom aggregates (`aggregation.py:76`, `528-529`).
- Optional dependency errors: `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:48-50`, `renderers/pdf.py:42-44`) — covered by `pytest.importorskip` in tests.
- Aggregation never catches exceptions: a failing expression propagates up through `run()` to the caller.

## Cross-Cutting Concerns

**Logging:** No logging framework — the library is pure and stateless; errors are raised, not logged (`logging` is not imported anywhere in `encino_rpt/`).
**Validation:** Two-tier — immediate builder validation (`report.py`, `section.py`) plus a final structural `_validate` pass in the engine (`aggregation.py:518-535`) that checks undeclared `source`s, undeclared `parent`s, and unregistered custom aggregates.
**Authentication:** Not applicable — this is an embeddable library with no server, no auth, no user context.
**Security:** Three independent defenses — (1) no `eval`, expressions go through the AST whitelist (`expressions.py`); (2) OWASP formula-injection sanitization for CSV/Excel (`renderers/_sanitize.py`); (3) HTML escaping and CSS property/value filtering for HTML output (`renderers/html.py:160-182`).

---

*Architecture analysis: 2026-09-17*
