<!-- refreshed: 2026-09-17 -->
# Architecture

**Analysis Date:** 2026-09-17

## System Overview

```text
┌───────────────────────────────────────────────────────────────────────┐
│                       Configuración (builder)                          │
│   `Report` (encino_rpt/report.py)  +  `Section` (encino_rpt/section.py)│
│              mutan especificaciones internas (encino_rpt/_specs.py)    │
└──────────────────────────────────┬────────────────────────────────────┘
                                   │ Report.run()
                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│                     Motor de agregación (in-memory)                    │
│   `build()` (encino_rpt/aggregation.py)                                │
│   helpers: expressions.py · template.py · charts.py · pivot.py         │
└──────────────────────────────────┬────────────────────────────────────┘
                                   │ produce
                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│                 Modelo canónico (pydantic, serializable)               │
│   `ReportResult` → `Group`/`Detail`/`Chart`/`Pivot`/`Kpi`/`Total`/...  │
│   (encino_rpt/models.py)                                               │
└──────────────────────────────────┬────────────────────────────────────┘
                                   │ render
                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│                      Renderers (patrón visitor)                        │
│   Html · Excel · Csv · Text · Pdf · Json (encino_rpt/renderers/)       │
│   todos consumen el walker compartido `_walk.py`                       │
└───────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Report` | Fluent builder: rows, params, computed fields, links, images, detail columns, groups, formats, styles, datasets, KPIs, custom functions/aggregates | `encino_rpt/report.py` |
| `Section` | Public facade that mutates a group's `GroupSpec` (header/footer/total/chart/pivot/order/top/suppress/page_break) | `encino_rpt/section.py` |
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

**Overall:** Layered pipeline: declarative fluent builder → in-memory aggregation engine → immutable canonical pydantic tree → visitor-based renderers.

**Key Characteristics:**
- Fluent builder API returning `self` for chaining (`report.py`, `section.py`).
- Spec objects (`_specs.py`) decouple what the user declared from the canonical output.
- Two-phase total resolution: base totals first, then deferred expressions using `TOTAL("seccion.nombre")` (phase B in `aggregation.py:382-389`).
- Post-processing phase C: `order_by`, `top(n)`, `suppress_zero` applied after totals are computed, before charts/pivots are appended (`aggregation.py:304,321-331`).
- Pydantic v2 models with typed discriminators (`type: Literal[...]`) for polymorphic children.
- Shared iterative `walk()` generator centralizes the visitor traversal that each renderer previously duplicated (`encino_rpt/renderers/_walk.py`).
- Lazy imports for all optional renderer dependencies (`openpyxl`, `reportlab`) and even required internal modules to break import cycles.
- In-memory aggregation engine; heavy aggregates are a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).

## Layers

**Configuration (builder):**
- Purpose: Declarative configuration of a report.
- Location: `encino_rpt/report.py`, `encino_rpt/section.py`, `encino_rpt/_specs.py`.
- Contains: The `Report` builder, the `Section` facade, and internal `*Spec` dataclasses.
- Depends on: `encino_rpt/_specs.py`, `encino_rpt/models.py` (only `Format`, `ConditionalRule`, `ReportResult` for type hints).
- Used by: application code (see README examples).

**Engine:**
- Purpose: Enrich rows, build the group hierarchy, compute totals, assemble `ReportResult`.
- Location: `encino_rpt/aggregation.py` (with helpers `expressions.py`, `template.py`, `charts.py`, `pivot.py`).
- Contains: `build(report)`, `_validate`, `_visible_columns`, `_enrich`, partitioning, group-tree construction, total computation, deferred resolution, template resolution, KPI computation.
- Depends on: all `*Spec` types, all model types, `evaluate`, `render_template`, `build_chart`, `build_pivot`.
- Used by: only `Report.run()` (`encino_rpt/report.py:280-288`).

**Canonical model:**
- Purpose: Typed, JSON-serializable representation of the report result.
- Location: `encino_rpt/models.py`.
- Contains: 13 pydantic models (see Component Responsibilities table).
- Depends on: `pydantic>=2` only.
- Used by: the engine (writes), the renderers (read), and downstream consumers (`model_dump()` / `model_validate()` / `to_json()`).

**Rendering:**
- Purpose: Convert the canonical tree to a concrete output format.
- Location: `encino_rpt/renderers/` (`html.py`, `excel.py`, `csv.py`, `text.py`, `pdf.py`, `json.py`, `_walk.py`, `_format.py`, `_sanitize.py`).
- Contains: Visitor-style renderer classes + shared walker/formatting/sanitizing helpers.
- Depends on: `encino_rpt/models.py`; `openpyxl` and `reportlab` only inside `excel.py`/`pdf.py` (optional extras).
- Used by: `ReportResult` convenience methods and end users.

## Data Flow

### Primary Request Path (build a report)

1. User declares a `Report` via fluent methods (`add_field`, `group`, `detail`, `kpi`, ...) — `encino_rpt/report.py`.
2. `Report.run()` lazily imports `build` and delegates — `encino_rpt/report.py:280-288`.
3. `build()` validates specs and sources — `aggregation.py:441-458,462`.
4. `_visible_columns()` computes the final ordered column list (detail + inserted `after` fields) — `aggregation.py:430-438,463`.
5. `_enrich()` evaluates computed fields (expr/link/image) and cumulative sums per source — `aggregation.py:109-135,466-468`.
6. `_build_group_tree()` determines the root spec and parent→children map — `aggregation.py:139-158,470`.
7. `_build_group()` recursively partitions rows, builds `Group` nodes with totals, applies phase C ordering, then appends charts/pivots — `aggregation.py:177-318,473`.
8. `_resolve_deferred()` computes phase-B totals that reference `TOTAL(...)` — `aggregation.py:382-389,477`.
9. `_render_templates()` interpolates `{{...}}` into header/footer using `_first_row` context — `aggregation.py:393-411,478`.
10. `build()` returns `ReportResult` (meta, columns, formats, styles, kpis, root) — `aggregation.py:480-487`.

### Secondary Flow (render to a destination)

1. User calls a convenience method on `ReportResult` (`render_html`, `to_csv`, `to_excel`, `to_pdf`, `to_text`, `to_json`) — `encino_rpt/models.py:150-227`.
2. The method lazily imports the matching renderer and delegates — e.g. `models.py:160-162` (HTML), `models.py:211-213` (JSON).
3. The renderer calls the shared `walk(result.root)` generator — `encino_rpt/renderers/_walk.py:8-31`.
4. The renderer emits format-specific output per `(event, node)` pair (`group_start`, `group_end`, `detail`, `chart`, `pivot`).

**State Management:**
- All builder state lives in instance attributes of `Report` (`self._fields`, `self._groups`, `self._detail`, `self._datasets`, etc. — `encino_rpt/report.py:27-39`); there is no module-level mutable state.
- Engine state (`registry`, `deferred`, `sources`) is local to `build()` (`aggregation.py:466-473`) and threaded through private helper parameters.
- `Group` carries private, non-serialized context for late template rendering: `_first_row`, `_header_tpl`, `_footer_tpl` via pydantic `PrivateAttr` (`encino_rpt/models.py:123-126`).
- A fresh `Report` instance is required per report — `run()` does not reset the builder, so re-running `run()` re-executes the full aggregation.

## Key Abstractions

**Canonical tree (`ReportResult`):**
- Purpose: The serializable contract between engine and presentation; pure data.
- Location: `encino_rpt/models.py:136-228`.
- Pattern: pydantic `BaseModel` with typed children (`root: Group`), convenience render methods with lazy imports, `to_json` with `schema_version`.
- Serialization: `model_dump()` / `model_validate()` round-trip verified in `tests/test_report.py`.

**Spec vs. model:**
- Purpose: `GroupSpec` records what a cut (group) declares; `Section` is the public handle that mutates it. Specs are mapped to canonical models during `build()` and never appear in the output tree.
- Location: `encino_rpt/_specs.py:77-96`, `encino_rpt/section.py`.
- Pattern: dataclass spec mutated via fluent facade; `group()` returns a `Section`, `section(name)` re-opens it (`report.py:224-278`).

**Safe expression evaluator:**
- Purpose: Computed fields, conditional totals, and ordering expressions.
- Location: `encino_rpt/expressions.py:54-63`.
- Pattern: `ast.parse(mode="eval")` + strict whitelist walk (`_walk`, `expressions.py:66-118`); no `eval`.
- Safety: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:45-47`).

**Shared tree walker:**
- Purpose: Uniform tree walking across all output formats.
- Location: `encino_rpt/renderers/_walk.py`.
- Pattern: iterative generator `walk(root)` yielding `("group_start", Group)`, `("group_end", Group)`, `("detail", Detail)`, `("chart", Chart)`, `("pivot", Pivot)` in document order, with an explicit closing marker so renderers can emit totals/footer after children.
- Extension: add a new renderer class that consumes `walk()` and implement `render(result)`; register it in `encino_rpt/renderers/__init__.py`.

**Path-group trie:**
- Purpose: Group rows by a dotted path column (`"1.2.3"`) into a nested hierarchy without recursion-depth limits.
- Location: `encino_rpt/aggregation.py:214-274` (`_PathNode`, `_make_path_node`, `_segs`).
- Pattern: iterative trie built once per row (split cached), then expanded to `Group` nodes via an explicit stack.

## Entry Points

**Package public API:**
- Location: `encino_rpt/__init__.py`.
- Triggers: `from encino_rpt import Report, ReportResult, Group, Total, ...`.
- Responsibilities: re-export the builder and canonical model types; `__all__` lists 14 public names (`__init__.py:20-34`). `Section` is intentionally NOT exported (reachable via `Report.group()`/`Report.section()`).

**Report execution:**
- Location: `encino_rpt/report.py:280-288`.
- Triggers: user call after declaring the report.
- Responsibilities: materialize the canonical `ReportResult` by delegating to `aggregation.build(self)`.

**Rendering:**
- Location: `encino_rpt/models.py:150-227` (`render_html`, `to_csv`, `to_text`, `to_excel`, `to_json`, `to_pdf`).
- Triggers: end-user call on the result.
- Responsibilities: lazy-import the matching renderer and delegate; never mutate the tree.

## Architectural Constraints

- **Threading:** Single-threaded, in-memory aggregation. No threads, no async, no shared state outside the `Report` instance. Engine helpers in `aggregation.py` are module-level functions with private `_`-prefixed names.
- **Global state:** None at module level. All mutable state is per-`Report` instance or local to `build()`.
- **Circular imports:** Avoided. `report.py` imports `aggregation.py` lazily inside `run()` (`report.py:286`); `models.py` imports renderers lazily inside convenience methods (`models.py:160-227`). `aggregation.py` imports `expressions.py`, `template.py`, `charts.py`, `pivot.py`, `models.py`, `_specs.py` at top level — one direction, no cycles.
- **No `eval`:** All expressions go through the AST whitelist walker (`expressions.py`). `ast.parse` node/depth counts are capped to prevent DoS.
- **Optional dependencies isolated:** `openpyxl` is imported only inside `ExcelRenderer.render` (`renderers/excel.py:42-46`); `reportlab` only inside `PdfRenderer.render` (`renderers/pdf.py:30-41`). Both raise `ImportError` with a hint to install the `excel`/`pdf` extras.
- **Python version:** `requires-python = ">=3.10"` (`pyproject.toml:13`); CI matrix runs 3.10–3.13. Code uses `from __future__ import annotations` throughout.
- **Pydantic forward references:** `Group.children` is a recursive union, resolved with `Group.model_rebuild()` at the bottom of `encino_rpt/models.py:230`.

## Anti-Patterns

### Tight coupling between `aggregation.py` and private `Report` attributes

**What happens:** `aggregation.py` reaches into `Report` internals directly: `report._rows`, `report._datasets`, `report._fields`, `report._functions`, `report._groups`, `report._order`, `report._kpis`, `report._aggregates` (`encino_rpt/aggregation.py:109-135,139-158,187-203,414-427,430-458`).
**Why it's wrong:** The engine is coupled to the builder's private state; renaming or restructuring `Report` internals silently breaks the engine.
**Do this instead:** Prefer adding accessor methods on `Report` (e.g. `report.sources()`, `report.group_specs()`) if the coupling grows.

### Charts/pivots appended after phase-C ordering

**What happens:** In `_build_instance`, `order_by`/`top`/`suppress_zero` are applied to `node.children` first (`aggregation.py:304`), and only then are chart/pivot extras appended (`aggregation.py:306-316`).
**Why it's wrong:** Charts and pivots are immune to `top(n)`/`suppress_zero` filtering, so a `top(3)` report can still show a chart over the full (unfiltered) child set.
**Do this instead:** If ordering/filtering should govern extras, derive chart/pivot inputs from the already-filtered children rather than the raw `child_pairs`/`rows`.

### Duplicated operator/format tables per renderer

**What happens:** `_OPS` in `html.py:12-19` and `_COLOR_OPS` in `excel.py:10-17` duplicate the same comparison-operator lambdas, and each renderer re-implements `_walk`/`_collect` logic (though they now share `walk()` from `_walk.py`).
**Why it's wrong:** The traversal is now shared, but operator dispatch and label/format fallbacks (`t.label or t.name or t.operator`) are still copy-pasted across `html.py:69`, `csv.py:50`, `text.py:46`, `pdf.py:86`, `excel.py:103`.
**Do this instead:** Extract a shared operator table and a `total_label(t)` helper into `renderers/_format.py` or a new `_common.py`.

## Error Handling

**Strategy:** Validate early (builder methods raise immediately), wrap engine failures with readable Spanish context, and re-raise optional-dependency errors with install hints. The engine never silently swallows exceptions.

**Patterns:**
- Builder validation: `group()` raises `ValueError` when `columns` and `path` are both set (`report.py:247-248`) and on duplicate cut names (`report.py:249-250`); `section()` raises `KeyError` for undeclared cuts (`report.py:275-277`); `Section.order_by` raises `ValueError` for invalid direction (`section.py:130-131`).
- Engine context wrapping: `_wrap()` re-raises any error as `AggregationError` with a `{context}: ...` prefix (`aggregation.py:27-36`).
- Expression errors: `ExpressionError(ValueError)` for unknown names, unsafe nodes, complexity/depth/pow limits (`expressions.py:50-118`).
- Template errors: `ValueError` for non-numeric `param.` indexes, `IndexError` for out-of-range params, `KeyError` for unresolved tokens (`template.py:23-29`).
- Aggregate errors: `ValueError` for unknown operators (`aggregation.py:61`); `AggregationError` for unregistered custom aggregates (`aggregation.py:69,452`).
- Optional dependency errors: `ImportError` with install hints for `openpyxl`/`reportlab` (`renderers/excel.py:46`, `renderers/pdf.py:41`) — covered by `pytest.importorskip` in tests.
- Aggregation never catches exceptions: a failing expression propagates up through `run()` to the caller.

## Cross-Cutting Concerns

**Logging:** Not used. The library is pure and stateless; errors surface via exceptions. No `logging` imports anywhere in `encino_rpt/`.
**Validation:** `_validate()` checks that `source`/`parent` references resolve and custom aggregates are registered (`aggregation.py:441-458`); pydantic validates the canonical tree on construction.
**Authentication:** Not applicable — the library has no network, DB, or auth surface.
**Security:** Expression sandbox (AST whitelist, no `eval` — `encino_rpt/expressions.py`); formula-injection protection for CSV/Excel (`encino_rpt/renderers/_sanitize.py`, tested in `tests/test_security.py`); HTML escaping + style-property whitelist regex `_SAFE_PROP` (`renderers/html.py:21-22,135-157`).

---

*Architecture analysis: 2026-09-17*
