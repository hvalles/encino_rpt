# Codebase Concerns

**Analysis Date:** 2026-09-16

Scope: full repo — `encino_rpt` (report builder + renderers), `tests/`, `docs/`, CI.

## Tech Debt

**`Report.run()` is not idempotent — re-running doubles group children:**
- Issue: `_build_group_tree` mutates the internal `GroupSpec.children` list via `append` on every run (`encino_rpt/aggregation.py:128-137`). Calling `run()` twice appends every `GroupSpec` to its parent twice.
- Files: `encino_rpt/aggregation.py:117-137`, `encino_rpt/report.py:278-286`
- Impact: Confirmed — `rep.run(); rep.run()` on a 2-agent report yields 4 root children instead of 2. Any caller that caches and re-runs a `Report` gets duplicated sections, double-counted totals, and confusing output.
- Fix approach: Make `_build_group_tree` build a fresh tree (copy `GroupSpec` per run, or derive children adjacency from `_order` + `parent` without mutating the specs in place).

**Declared-but-unimplemented features (design vs. implementation gap):**
- Issue: `docs/design/10-report.md` (§8 mapping table, decisions #15/#29) promises Link→`<a>`/hyperlink/`<img>`, `page_break` page breaks in PDF/HTML, `repeat_header` in HTML, and `column_position` alignment. None are implemented in any renderer.
- Files:
  - `encino_rpt/models.py:117-119` — `show_collapsed`, `default_collapsed`, `page_break` stored on `Group`; `models.py:53` — `column_position` on `Total`
  - `encino_rpt/_specs.py:38,84-86,90` — same fields carried in specs
  - `encino_rpt/renderers/pdf.py:64` — only `repeat_header` used (PDF); `page_break` never read
  - `encino_rpt/renderers/html.py:26-28` — `repeat_header` stored, never used anywhere in the renderer
- Impact: Confirmed — a `link()`/`image()` column renders as the pydantic repr (`type='link' target='report' href='/pedido/1' label='Ver' params={}`) in CSV, HTML, text and PDF output. `Section.page_break()` has zero effect on output. `column_position`/`footer_column_position` are dead hints. Callers relying on the documented behavior get text soup instead of links/images.
- Fix approach: Either implement Link/Image handling in `html.py` (anchor/img tags), `excel.py` (`cell.hyperlink`), `csv.py` (`label`/`href` text) and honor `page_break` in `pdf.py` (`PageBreak()`), or strip the dead fields/parameters and update the docs to match reality.

**Unused runtime dependency `encino-orm`:**
- Issue: `pyproject.toml:33` declares `encino-orm>=0.2.1` as a hard runtime dependency, but nothing in `encino_rpt/` or `tests/` imports it (the package consumes plain `list[dict]`).
- Files: `pyproject.toml:32-35`
- Impact: Every install pulls in an unnecessary package (and its transitive deps) for a pure-in-memory library that only needs `pydantic`.
- Fix approach: Remove `encino-orm` from `dependencies` (keep it in an optional dev/example group if needed for integration docs).

**Raw, context-free exceptions escape the aggregation pipeline:**
- Issue: `_value_for`/`evaluate` callers in the enrichment/aggregation loop (`encino_rpt/aggregation.py:53,102,173`) do not wrap per-expression errors. Confirmed: a total `expression="a/0"` raises a bare `ZeroDivisionError`; an unregistered `custom:` aggregate raises a bare `KeyError` (`aggregation.py:51`); an unknown expression name raises `ExpressionError`. All abort the entire `run()` with no indication of which group/row/field failed.
- Files: `encino_rpt/aggregation.py:48-62,90-113,166-179`, `encino_rpt/expressions.py:50-109`
- Impact: One bad row in a large dataset kills the whole report with a stack trace that gives no context. Hard to diagnose in production.
- Fix approach: Wrap row/field evaluation with a contextual error (group name, field name, row index) and/or continue-on-error policy.

**Silent failure modes mask configuration mistakes:**
- Issue: An unknown `source=` on a group falls back to the main dataset (`sources.get(spec.source, sources[None])` at `encino_rpt/aggregation.py:157`, and `report._datasets.get(source, [])` at `aggregation.py:91`). Unknown template tokens render as empty string (`encino_rpt/template.py:28` — `ctx.get(token, "")`). A typo like `{{totals.monto}}` renders `x=` silently.
- Files: `encino_rpt/aggregation.py:91,157`, `encino_rpt/template.py:18-28`
- Impact: Wrong dataset or a typo'd template header produces subtly wrong reports (empty headers, wrong numbers) with no warning. Confirmed: `render("x={{totals.monto}}", {...})` → `"x="`.
- Fix approach: Raise on unknown `source=` at declaration/run time; raise (or emit a strict-mode warning) on unresolved `{{token}}` instead of empty-string substitution.

## Known Bugs

**Excel `formulas=True` emits `SUM` ranges that double-count subtotals and chart aux data:**
- Symptoms: With nested groups and/or charts, the group `SUM` range spans every row written between the group start marker and the total — including child subtotal rows and chart scratch data.
- Files: `encino_rpt/renderers/excel.py:79-96` (`start`/`_sum_formula`) and `excel.py:168-199` (`_chart` writes aux rows in the same columns)
- Trigger: `global.total("sum", "total")` with `to_excel(formulas=True)` over grouped+charted data.
- Confirmed: output contains `B10: =SUM(B2:B9)` covering child subtotal rows (B3, B5) and chart series data (B8) — the "global total" of a 300-value report becomes 700.
- Fix approach: Track the exact detail-row span per group (record row range only over `Detail` children), or compute SUM per contiguous leaf range and subtract/avoid dupes; exclude chart aux rows from the range.

**Excel total rows bypass formula-injection sanitization:**
- Symptoms: `_total_row` writes the label and value with raw `ws.cell(...)` (`encino_rpt/renderers/excel.py:141-142`) instead of `write_excel_cell`; column headers are written raw too (`excel.py:66`).
- Trigger: A total label/name like `=1+1` or a column named `=HYPERLINK("x")`.
- Confirmed: cell A4 written as `data_type='f'` (live formula) for a label `=1+1`.
- Fix approach: Route every cell write through `_sanitize.write_excel_cell` (`encino_rpt/renderers/_sanitize.py:20-27`), including headers and total rows.

**`format_value` loses precision on large numbers when `decimals=None`:**
- Symptoms: `Format()` defaults `decimals=None`; the formatter uses `f"{abs(num):g}"` (`encino_rpt/renderers/_format.py:29`) which truncates to 6 significant digits and emits scientific notation.
- Confirmed: `format_value(1000000.5, Format())` → `'1e+06'`; `format_value(1234567.89, Format())` → `'1.23457e+06'`. Catastrophic for a financial reporting library.
- Files: `encino_rpt/renderers/_format.py:21-38`
- Fix approach: Use `repr`/full-precision formatting (e.g. `str(num)` or `f"{num:.10g}"` with a higher guard) when `decimals is None`, and add a regression test for 7+ digit values.

**`order_by(total=...)` with a missing/unmatched total name crashes with raw `TypeError`:**
- Symptoms: `_sort_key` returns `None` when the named total isn't found (`encino_rpt/aggregation.py:294-298`), then `sorted` compares `None` against `None`/numbers.
- Confirmed: `TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'`.
- Files: `encino_rpt/aggregation.py:277-307`
- Fix approach: Raise a clear error at run time naming the missing total, or define a total-ordered fallback key (e.g. `-inf` sentinel).

**`order_by(expression=...)` evaluates without the report's custom functions:**
- Symptoms: `_sort_key` calls `evaluate(expression, ..., {})` with an empty functions dict (`encino_rpt/aggregation.py:300`), while every other evaluation site passes `report._functions`.
- Confirmed: `order_by(expression="doblado(monto)")` after `add_function("doblado", ...)` raises `ExpressionError: función no permitida: 'doblado'`.
- Files: `encino_rpt/aggregation.py:290-307`
- Fix approach: Thread `report._functions` into `_apply_order`/`_sort_key` (and `report._aggregates` where relevant).

**`run()` idempotency** — see Tech Debt (first item); it is a correctness bug, not just debt.

## Security Considerations

**CSS injection in HTML conditional styles:**
- Risk: Inline `style` attribute values are HTML-escaped but not CSS-escaped (`encino_rpt/renderers/html.py:108-124`). A style value containing `;` injects arbitrary CSS declarations inside the quoted attribute.
- Confirmed: `add_style("total", when="lt", value=0, background="red;position:fixed")` renders `style="background:red;position:fixed"` — unbounded extra declarations (still HTML-escaped, so `"` cannot break the attribute, but `position:fixed;opacity:0` overlays/UI-redress are possible).
- Files: `encino_rpt/renderers/html.py:108-124`, `tests/test_security.py:45-54` (only tests `"` and property-name injection, not `;` values)
- Current mitigation: property names validated by `_SAFE_PROP` (`html.py:20`); attribute quoting via `_esc`.
- Recommendations: Reject or encode `;`/whitespace-injection characters in style values, or validate values against a strict allowlist (colors/lengths only).

**Excel formula injection gaps beyond detail cells:**
- Risk: `_sanitize.write_excel_cell` covers detail/KPI/pivot/chart cells, but total labels/values and column headers bypass it (see Known Bugs). A user-supplied label starting with `=` becomes a live formula when the file is opened.
- Files: `encino_rpt/renderers/excel.py:66,141-142`, `encino_rpt/renderers/_sanitize.py:20-27`
- Recommendations: Route all writes through `write_excel_cell`.

**CSV formula-injection sanitizer bypassable with a leading space:**
- Risk: `is_dangerous` checks `value.startswith(("=", "+", "-", "@", "\t", "\r"))` (`encino_rpt/renderers/_sanitize.py:5`) — a value like `" =1+1"` (leading space, common in pasted data) or `"\x0c=1+1"` passes through unsanitized and Excel still evaluates it (Excel tolerates a leading space before `=`).
- Files: `encino_rpt/renderers/_sanitize.py:5-17`, used by `encino_rpt/renderers/csv.py:31-58`
- Current mitigation: simple prefix list.
- Recommendations: Trim/scan whitespace (`value.lstrip().startswith(...)`) per OWASP guidance; also prefix a `'` when the value contains a leading BOM/whitespace followed by a dangerous char.

**Expression evaluator DoS edge cases leak raw exceptions:**
- Risk: `_MAX_POW_EXP` is only enforced when the exponent is an `int` (`encino_rpt/expressions.py:80-81`); a float exponent like `2 ** 1e100` bypasses the check and raises a raw `OverflowError`. Pathologically nested expressions can raise `RecursionError` from `ast.parse` before the node-count guard runs.
- Files: `encino_rpt/expressions.py:44-60,80-81`
- Current mitigation: `_MAX_NODES`/`_MAX_DEPTH`/`_MAX_POW_EXP` guards (`expressions.py:45-47`), covered by `tests/test_security.py:31-41`.
- Recommendations: Guard `Pow` for both int and float exponents; catch `RecursionError`/`MemoryError` around `ast.parse` and re-raise as `ExpressionError`; add regression tests.

## Performance Bottlenecks

**Pivot row/column totals are quadratic in unique values:**
- Problem: `build_pivot` computes `row_totals` and `col_totals` by rescanning all rows per unique value (`encino_rpt/pivot.py:28-33`) — O(rows × uniques). A pivot over a high-cardinality column (e.g. 50k rows × 10k SKUs) does 500M row visits.
- Files: `encino_rpt/pivot.py:14-43`
- Improvement path: Accumulate row/column totals in the same single pass that builds `buckets` (`pivot.py:19-26`).

**Path groups re-split every row at every level and recurse unboundedly:**
- Problem: `_make_path_node` calls `_segs` for every row at every level (`encino_rpt/aggregation.py:190-231`), so a row at depth D is split D+1 times (O(n × depth)). Recursion depth equals the path depth, so `aggregation.py:217-228` hits Python's default recursion limit — confirmed `RecursionError` with a 1200-segment path.
- Files: `encino_rpt/aggregation.py:182-231`
- Improvement path: Split each row's path once up front and bucket by segment arrays; use an iterative (stack-based) tree builder to remove the recursion limit.

**Full-row dict copies per field and per dataset:**
- Problem: `_enrich` copies each row (`dict(row)` at `encino_rpt/aggregation.py:95`) for the main dataset and again for every `add_dataset` source; the report also retains the raw `_rows`/`_datasets` list for the lifetime of the `Report` object. Peak memory ≈ 2× input + copies.
- Files: `encino_rpt/aggregation.py:90-113`, `encino_rpt/report.py:27-38`
- Improvement path: Acceptable for in-memory design (documented non-objective in `docs/design/10-report.md:36-39` — heavy aggregates belong in SQL `ROLLUP`/`CUBE`); consider lazily enriching datasets only when referenced.

## Fragile Areas

**`encino_rpt/aggregation.py` — the whole build pipeline:**
- Files: `encino_rpt/aggregation.py:117-406`
- Why fragile: It mutates shared `GroupSpec` objects (`_build_group_tree` appends children; `_apply_order` re-sorts in place), depends on declaration order (`parent` must precede child, otherwise the child silently attaches to root — `aggregation.py:128-136`), silently tolerates duplicate group names (`report.py:257` overwrites while `_order` appends twice → duplicated children on the next run), and mixes presentation (chart/pivot build) into aggregation.
- Safe modification: Treat `GroupSpec` as immutable input; build a fresh internal node graph per `run()`; validate parent names, duplicate names, and `custom:` names up front.
- Test coverage: `tests/test_report.py` covers happy paths only — no tests for `run()` twice, parent-declared-after-child, duplicate group names, or missing datasets.

**Renderer traversal duplicated with divergent edge behavior:**
- Files: `encino_rpt/renderers/html.py:51-101`, `encino_rpt/renderers/csv.py:35-57`, `encino_rpt/renderers/text.py:27-55`, `encino_rpt/renderers/excel.py:72-114`, `encino_rpt/renderers/pdf.py:77-103`
- Why fragile: Five hand-maintained copies of the same tree walk with subtly different handling (Excel keeps per-group `start` state and a mutable `self._ws`/`self._row`/`self._result` on the instance — a shared `ExcelRenderer` instance is not re-entrant for concurrent renders; CSV emits rows without a trailing newline; PDF nests pivot tables inside table cells). Fixes to one renderer (e.g. the `SUM` range bug) must be replicated across the others.
- Safe modification: Extract a shared iterator that yields typed "rows" (group header, detail, total, chart, pivot) once, and have each renderer consume it; make `ExcelRenderer.render()` use locals instead of instance state.

**`encino_rpt/expressions.py` — the whitelist evaluator:**
- Files: `encino_rpt/expressions.py:54-109`
- Why fragile: Any new operator/function must be whitelisted here and in `docs/security.md`; raw arithmetic exceptions (`ZeroDivisionError`, `OverflowError`) and parse-level `RecursionError` escape without `ExpressionError` wrapping; `evaluate` is called from 4 sites (`aggregation.py:53,102,173,300`) with inconsistent function-dict arguments (one passes `{}`).
- Test coverage: `tests/test_report.py:8-39`, `tests/test_security.py:31-41` — good rejection coverage; missing float-exponent and deep-nesting cases.

## Scaling Limits

**In-memory aggregation on full result sets:**
- Current capacity: Entire `list[dict]` input held in memory; copied once per dataset in `_enrich` (`encino_rpt/aggregation.py:90-113`).
- Limit: Memory-bound; design doc explicitly defers heavy aggregates to SQL `GROUP BY ROLLUP`/`CUBE` (`docs/design/10-report.md:36-39`).
- Scaling path: Pre-aggregate in SQL; use the report builder only for assembly/presentation, per the documented design.

**Path-group depth limited by Python recursion (~1000):**
- Current capacity: reliable to ~900 segments per path.
- Limit: `RecursionError` at deeper hierarchies (confirmed at 1200).
- Scaling path: iterative builder in `_make_path_node`.

**Pivot cardinality:**
- Limit: O(rows × unique values) for totals (`encino_rpt/pivot.py:28-33`); see Performance.

## Dependencies at Risk

**`pydantic>=2` (runtime core):**
- Risk: Only hard dependency; `Group` uses forward refs + `model_rebuild()` (`encino_rpt/models.py:121,217`); `Link`/`Image`/`Total` carry unconstrained `Any` fields (`models.py:17,52,77`), so schema drift between `model_dump` and `model_validate` round-trips is theoretically possible.
- Impact: Low — pinned `>=2`, tested round-trip in `tests/test_report.py:235-243`.
- Migration plan: None needed; add a CI job on pydantic 2.x latest to catch breaking releases early.

**`encino-orm>=0.2.1`:** unused hard dependency — see Tech Debt.

**`openpyxl` / `reportlab` (optional extras):**
- Risk: Only exercised via `pytest.importorskip` in tests (`tests/test_report_renderers.py:67,84,100,113`); the `excel`/`pdf` extras are not installed by the default `uv sync --group dev` — CI only installs them via the `dev` group in `pyproject.toml:50-55` (they are also listed there), so CI does exercise them.
- Impact: Low. `docs.yml`/`publish.yml` workflows don't run tests against them by default but `ci.yml:24` (`uv sync --all-extras --group dev`) does.

## Missing Critical Features

**Link/Image columns are not rendered as links/images anywhere** (see Tech Debt). The `Link`/`Image` models, the `Report.link()`/`Report.image()` builders, and the `<a>`/`<img>` output promised in the design doc exist, but all five renderers fall back to `str(pydantic_model)`.

**`page_break`, `show_collapsed`/`default_collapsed`, `column_position`** have no rendering effect (see Tech Debt).

## Test Coverage Gaps

**Untested areas:**
- Multi-dataset (`add_dataset` + `source=`) — zero tests, yet it is a headline feature with silent-fallback behavior (`aggregation.py:91,157`).
- Excel chart and pivot rendering (`excel.py:168-215`), PDF pivot (`pdf.py:105-114`) — rendered but never asserted aside from byte-magic.
- `run()` called twice on the same `Report` (idempotency bug — see above).
- `order_by` with `expression=`, missing totals, `suppress_zero` with column vs total — only `order_by(total=...)` happy path tested (`tests/test_report.py:182-195`).
- Cumulative fields with non-zero `start`; conditional totals with `count`.
- Error paths: unknown `source=`, unregistered `custom:` aggregate, division by zero, unknown template tokens.
- Large-number formatting (`format_value` precision bug).
- Link/Image output content in renderers.
- Deep path hierarchies (>900 levels) — RecursionError.

- Files: `tests/test_report.py` (269 lines), `tests/test_report_renderers.py` (120 lines), `tests/test_security.py` (63 lines)
- Risk: High — the Excel `SUM` double-count and precision bugs shipped despite the suite passing.
- Priority: High

**CI gaps:**
- `.github/workflows/ci.yml:29-30` runs `ruff check` and `pytest` only — no type checker (mypy/pyright), no `ruff format --check`, no coverage gate, no performance/smoke benchmark for large inputs.
- Priority: Medium

---

*Concerns audit: 2026-09-16*