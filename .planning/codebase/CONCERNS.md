# Codebase Concerns

**Analysis Date:** 2026-09-17

## Known Bugs

**`detail(source=...)` is silently ignored (multi-query detail no-op):**
- Symptoms: Passing `source="presupuesto"` to `Report.detail(...)` has no effect; detail rows are always taken from the primary dataset.
- Files: `encino_rpt/report.py:211-222` — `def detail(self, *columns, source=None)` stores `self._detail = list(columns)` and never uses `source`.
- Trigger: `rep.add_dataset("presupuesto", rows)` then `rep.detail("monto", source="presupuesto")`.
- Impact: Multi-query detail is documented in the design contract (`docs/design/10-report.md:890`) and advertised in `README.md:42`, but does not work. Only `group`/`chart`/`pivot`/`add_field`/`kpi` honor `source=` (`aggregation.py:178,420`).
- Workaround: None — detail-level `source` cannot be expressed.

**Named totals that resolve to `None` crash the registry:**
- Symptoms: `TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'` during `run()`.
- Files: `encino_rpt/aggregation.py:203` — `registry[key] = registry.get(key, 0) + val` runs outside the `_wrap(...)` guard.
- Trigger: A named total (`total(..., name="x")`) using `avg`, `max`, `min`, or `count_distinct` over a group whose values are all `None` returns `None` (`aggregation.py:52-60`), then `0 + None` raises.
- Workaround: Avoid naming totals that can be empty, or ensure the column is non-null.

**`suppress_zero(column=...)` with a missing column removes every child:**
- Symptoms: All children of a section disappear when `suppress_zero` references a column not present in the grouping key.
- Files: `encino_rpt/aggregation.py:362-378` (`_is_zero`) — `v = child.key.get(column)` yields `None` when the column is absent, and `return v is None or v == 0` returns `True`.
- Trigger: `rep.section("x").suppress_zero(column="columna_inexistente")`.
- Workaround: Only suppress on columns that are actually part of the grouping key or detail. (Tracked in `.planning/PROJECT.md:51`.)

**Unhashable grouping/pivot values raise raw `TypeError`:**
- Symptoms: `TypeError: unhashable type: 'list'` (or `'dict'`) when a grouping column holds a list/dict (e.g. a JSON column).
- Files: `encino_rpt/aggregation.py:167` (`key = tuple(r.get(c) for c in spec.columns)`), `encino_rpt/pivot.py:25` (`buckets.setdefault((rv, cv), [])`) and `encino_rpt/pivot.py:47-54` (`_ordered_unique` uses `set`).
- Trigger: Grouping or pivoting by a column whose values are non-hashable.
- Workaround: Materialize/stringify the column before grouping.

**Missing/`None` path column produces a spurious `"None"` segment:**
- Symptoms: A `path=` group over a column with `None`/missing values creates a literal `"None"` hierarchy segment.
- Files: `encino_rpt/aggregation.py:211` — `_segs` does `str(r.get(spec.path, ""))`, so `None` becomes `"None"`.
- Trigger: Rows lacking the path column or holding `None`.
- Workaround: Guarantee non-null path values, or filter rows beforehand.

**`count` over an expression counts truthy values, not rows:**
- Symptoms: `count` with an `expression=` yields a different result than `count` without one.
- Files: `encino_rpt/aggregation.py:73-74` — `sum(1 for v in vals if v)` (truthy count) vs. `aggregation.py:78-79` — `len(rows)` (row count).
- Trigger: `section.total("count", expression="IF(monto > 0)")` returns the count of non-zero results, not the number of rows.
- Workaround: Use `count_distinct` or a `sum` expression to disambiguate; semantics are undocumented.

## Tech Debt

**Engine couples tightly to private `Report` state:**
- Issue: `aggregation.py` reads `report._rows`, `report._datasets`, `report._fields`, `report._functions`, `report._groups`, `report._order`, `report._aggregates`, `report._kpis`, `report._detail`, `report._formats`, `report._styles`, `report._params`, `report._title` directly (e.g. `aggregation.py:91-135,385-458`). `_sort_key`/`_is_zero` also read the private pydantic attr `child._first_row` (`aggregation.py:348,362-378`).
- Impact: Any rename or refactor of the builder's internal layout breaks the engine; the coupling cannot be caught by tests alone.
- Fix approach: Add accessor methods/properties on `Report` (e.g. `report.datasets`, `report.fields`) and thread an explicit context object through `build()` rather than reaching into `_`-prefixed attributes.

**Duplicated comparison-operator dispatch tables:**
- Issue: The same `lt/le/gt/ge/eq/ne` lambda tables are defined three times — `_OPS` in `encino_rpt/renderers/html.py:12-19`, `_COLOR_OPS` in `encino_rpt/renderers/excel.py:10-17`, and `_CMP` in `encino_rpt/expressions.py:21-28`.
- Impact: Divergence risk (a new comparison operator must be added in three places); no single source of truth.
- Fix approach: Extract a shared `compare(op, a, b)` helper into a small internal module.

**`footer(column_position=...)` is a dead parameter:**
- Issue: `Section.footer(column_position=...)` stores `footer_column_position` (`encino_rpt/section.py:37`, `_specs.py:90`), but it is never read by `aggregation.py` or any renderer (grep confirms write-only). Contrast `Total.column_position`, which is honored by `excel.py:105`.
- Impact: Users pass a layout hint that silently does nothing.
- Fix approach: Either implement footer alignment in the renderers or remove the parameter and document it.

**`ExcelRenderer` `styles` parameter/attribute is dead:**
- Issue: `ExcelRenderer.__init__(styles=...)` stores `self.styles` (`encino_rpt/renderers/excel.py:24`) but never uses it; `render(..., styles=None)` accepts `styles` (`excel.py:27`) and ignores it. `ReportResult.to_excel(styles=...)` (`encino_rpt/models.py:187-200`) threads the value through, but nothing styles the worksheet.
- Impact: The "additional styles" option in `to_excel(styles=...)` is a no-op.
- Fix approach: Wire `self.styles` into `_write_value`/`_full_row`/`_total_row`, or drop the parameter.

**Codebase-map docs are stale relative to the code:**
- Issue: `AGENTS.md` (and its embedded STACK/CONVENTIONS/ARCHITECTURE) describe 5 renderers with per-renderer `_walk` visitors, but the code now has 6 renderers (`JsonRenderer`) plus a shared iterative traversal in `encino_rpt/renderers/_walk.py`. The STACK section still lists `encino-orm` as a declared dependency, though it was removed (DEP-01).
- Impact: New contributors and the planner/executor load incorrect context.
- Fix approach: Re-run the codebase map after Phase 8 to refresh STACK/ARCHITECTURE/CONVENTIONS.

**`ReportResult` docstring omits `to_json`:**
- Issue: `encino_rpt/models.py:139-141` lists `render_html`, `to_csv`, `to_text`, `to_excel`, `to_pdf` but not the newer `to_json` (`models.py:202-213`).
- Impact: Doc drift in the public API surface.

**`encino_rpt/__init__.py` import-alignment outlier:**
- Issue: `from .models import (...)` aligns items to column 21 (`encino_rpt/__init__.py:3-17`), inconsistent with the one-item-per-line style used elsewhere (e.g. `renderers/__init__.py`).
- Impact: Cosmetic; `ruff check` does not flag it.

## Security Considerations

**`evaluate` does not wrap `ValueError` from `ast.parse` on null bytes:**
- Risk: An expression string containing a null byte (`"\x00"`) makes `ast.parse` raise `ValueError("source code string cannot contain null bytes")`, which escapes as a raw `ValueError` instead of `ExpressionError`.
- Files: `encino_rpt/expressions.py:57-60` — only `RecursionError`/`MemoryError`/`SyntaxError` are caught.
- Current mitigation: None for this specific input.
- Recommendations: Catch `ValueError` (and `TypeError`) in the `ast.parse` guard and re-raise as `ExpressionError`, matching the other malformed-input cases.

**JSON renderer `schema_version` key could be silently overridden:**
- Risk: `JsonRenderer.to_dict` builds `{"schema_version": SCHEMA_VERSION, **result.model_dump(mode="json")}` (`encino_rpt/renderers/json.py:27`). If a model field named `schema_version` is ever added, the spread silently overwrites the constant.
- Current mitigation: None today (no such field exists).
- Recommendations: Emit `schema_version` after the spread, or namespace it (`"meta": {"schema_version": ...}`), and pin it to the package version rather than the hardcoded `"1.0"`.

**Excel formula mode intentionally bypasses cell sanitization:**
- Risk: When `formulas=True`, `_total_row` writes the generated `=SUM(...)` string via `ws.cell(self._row, col_idx, value)` directly, skipping `write_excel_cell` (`encino_rpt/renderers/excel.py:178`).
- Current mitigation: The formula string is generated internally by `_sum_formula` (`excel.py:138-158`) from row indices only — no user input — so it is safe today.
- Recommendations: Preserve this bypass only for internally-generated formulas; never pass user-controlled strings through this path. Add a regression test asserting user values are never written as live formulas in `formulas=True` mode.

## Performance Bottlenecks

**Deep trees survive `run()` and rendering but not JSON serialization:**
- Problem: Aggregation and renderers are iterative (deep path trees to depth 1100 are tested — `tests/test_report.py:418-436`, `tests/test_report_renderers.py:301-314`), but `model_dump()` / `model_validate()` / `json.dumps` on a deeply nested `Group.children` chain are recursive and may raise `RecursionError`.
- Files: `encino_rpt/models.py:121` (`Group.children`), `encino_rpt/renderers/json.py:23`.
- Cause: pydantic v2 serialization and `json.dumps` recurse over the nested model tree; the iterative `_walk` (`encino_rpt/renderers/_walk.py`) only helps the renderers.
- Improvement path: Add a test for `to_json()`/`model_dump()` on a >1000-deep path tree; if it fails, provide a depth-safe serialization path or document a max depth.

## Fragile Areas

**`ExcelRenderer` holds mutable render state on the instance:**
- Files: `encino_rpt/renderers/excel.py:51-54` (`self._ws`, `self._result`, `self._formulas`, `self._row`); also `PdfRenderer` sets `self._normal` (`encino_rpt/renderers/pdf.py:44`).
- Why fragile: `render()` is not re-entrant. Calling it twice on the same renderer instance overwrites `_ws`/`_result` and starts `_row` at 1 again; concurrent use of a shared renderer corrupts output.
- Safe modification: Keep all per-render state local to `render()` (pass `ws`/row counter explicitly) or document single-use and refuse reuse.

**Chart/pivot value errors are not wrapped with context:**
- Files: `encino_rpt/aggregation.py:308-316` — `build_chart`/`build_pivot` receive `_make_value_fn` lambdas and call them directly, unlike totals and KPIs which route through `_wrap` (`aggregation.py:194-198,421-425`).
- Why fragile: A bad expression or unknown aggregate in a chart/pivot raises a raw `ExpressionError`/`TypeError` with no group/field context, inconsistent with the error story elsewhere.
- Safe modification: Wrap `value_fn` calls in `_wrap` with a `"gráfico/pivote (grupo …)"` context label.
- Test coverage: No test exercises a failing chart/pivot expression.

**Empty-group aggregate semantics are asymmetric:**
- Files: `encino_rpt/aggregation.py:47-61`.
- Why fragile: `sum` → `0`, `count` → `0`, but `avg`/`max`/`min`/`count_distinct` → `None`. Downstream consumers must handle both, and numeric contexts (registry accumulation, ordering by total) can break on `None`.
- Safe modification: Document the `None`-vs-`0` contract explicitly, or make it uniform (e.g. return `None` for all empty aggregates).

## Scaling Limits

**In-memory design is a documented no-goal:**
- Current capacity: The library holds all rows and the full result tree in memory (`Report.__init__` copies rows into `self._rows`, `encino_rpt/report.py:27`).
- Limit: Memory-bound on large row sets; no streaming or SQL pushdown.
- Scaling path: Heavy aggregation is delegated to SQL `ROLLUP`/`CUBE` upstream (documented in `docs/design/10-report.md §11` and `REQUIREMENTS.md` "Out of Scope"). Not a defect, but a hard boundary to respect.

## Dependencies at Risk

**`pydantic>=2` has no upper bound:**
- Risk: `pyproject.toml:33` declares `pydantic>=2` unbounded. The entire model layer (`encino_rpt/models.py`) is pydantic v2, so a future pydantic minor bump can introduce deprecations or behavior changes silently.
- Impact: Breaking changes to `model_dump`/`model_validate`/`PrivateAttr` would ripple through serialization and the deep-tree path.
- Migration plan: Pin an upper bound (e.g. `<3`) or pin an exact tested minor in CI, and add a smoke test that exercises `model_dump`/`model_validate` round-trips on the Python matrix.

**Optional extras are unpinned at install time:**
- Risk: `[project.optional-dependencies]` lists `openpyxl` and `reportlab` with no version constraints (`pyproject.toml:37-38`); only `uv.lock` pins them.
- Impact: Users installing `encino-rpt[excel]`/`[pdf]` from PyPI get floating versions, so the published package's real dependency set is not reproducible outside `uv`.
- Migration plan: Add minimum-version constraints to the extras (matching the lockfile) so published installs are reproducible.

**Stale build artifacts in `dist/`:**
- Risk: `dist/` contains `encino_rpt-0.2.0` wheel/sdist while `pyproject.toml:10` declares `0.2.1`. The directory is gitignored, and `publish.yml` runs `uv build` (`.github/workflows/publish.yml:19`), so it regenerates — but locally the artifacts are misleading.
- Impact: Low; risk of accidentally shipping the old version if a manual release step is used.
- Migration plan: Delete `dist/` locally or rebuild before release.

## Missing Critical Features

**Multi-query detail rows:**
- Problem: `detail(source=...)` is accepted but non-functional (see Known Bugs). Per-dataset detail columns — a documented multi-query use case (`docs/design/10-report.md:890`, `README.md:42`) — cannot be produced.
- Blocks: Building a report whose detail section draws from a secondary `add_dataset` set.

**No shared operator/comparator module:**
- Problem: Comparison and arithmetic operators are re-declared across `expressions.py`, `html.py`, and `excel.py` (see Tech Debt), so adding a new operator requires touching multiple files.

## Test Coverage Gaps

**Multi-dataset happy path:**
- What's not tested: `add_dataset(name, rows)` + `source=` on `group`/`chart`/`pivot`/`add_field`/`kpi` has no end-to-end test. Only the design doc shows usage.
- Files: `tests/test_report.py`, `tests/test_report_renderers.py`.
- Risk: The `source` fallback (`sources.get(spec.source, sources[None])` in `aggregation.py:178`) and the field-source filtering (`aggregation.py:116`) are untested; regressions would go unnoticed.
- Priority: High.

**`suppress_zero` with a missing column:**
- What's not tested: The `_is_zero` false-positive that deletes all children (Known Bugs).
- Files: `encino_rpt/aggregation.py:362-378`; no test in `tests/`.
- Risk: Silent data loss in reports.
- Priority: High.

**Named totals returning `None`:**
- What's not tested: A named `avg`/`max`/`min`/`count_distinct` total over an all-`None` column crashes the registry (Known Bugs).
- Files: `encino_rpt/aggregation.py:203`.
- Risk: `TypeError` at runtime for valid reports.
- Priority: Medium.

**Unhashable grouping/pivot values:**
- What's not tested: Grouping or pivoting by a column holding lists/dicts (Known Bugs).
- Files: `encino_rpt/aggregation.py:167`, `encino_rpt/pivot.py:25,47-54`.
- Risk: Raw `TypeError` with no actionable message.
- Priority: Medium.

**Deep-tree JSON serialization:**
- What's not tested: `to_json()` / `model_dump()` on a >1000-deep path tree (only `run()` and text/HTML renderers are exercised at depth).
- Files: `tests/test_report.py:418-436`, `tests/test_report_renderers.py:301-314`.
- Risk: `RecursionError` in pydantic/json for deep hierarchies (see Performance).
- Priority: Medium.

**`detail(source=...)` behavior:**
- What's not tested: The no-op `source` parameter on `detail` (Known Bugs).
- Files: `encino_rpt/report.py:211-222`.
- Risk: The gap persists because no test asserts the documented behavior.
- Priority: Medium.

**`ExcelRenderer` `styles` and `footer(column_position=...)`:**
- What's not tested: Both features are dead (Tech Debt); no test would fail because neither is wired.
- Files: `encino_rpt/renderers/excel.py:24,27`, `encino_rpt/section.py:37`.
- Risk: The no-op behavior is silently accepted.
- Priority: Low.

**CI hardening (Phase 8 not started):**
- What's not enforced: CI runs only `pytest` and `ruff check` (`.github/workflows/ci.yml:26-30`). There is no type checker (`mypy`/`pyright`), no `ruff format --check`, no coverage gate, and no performance smoke test — all listed as Phase 8 success criteria (`ROADMAP.md:139-140`).
- Files: `.github/workflows/ci.yml`.
- Risk: Formatting drift and type errors can land unnoticed; coverage can regress without detection.
- Priority: High (this is the remaining planned phase).

---

*Concerns audit: 2026-09-17*
