# Codebase Concerns

**Analysis Date:** 2026-09-17

> Scope: full repo. Phases 1–8 complete (milestone `v1.0`). CI gaps (no type checker/format/coverage) are RESOLVED — mypy `2.3.1`, `ruff format --check`, coverage `fail_under=80`, and a split `test`+`quality` job matrix now run in `.github/workflows/ci.yml`. The engine bugs below are **documented, not fixed**; each carries a regression test (some `xfail(strict=True)`, others asserting the current behavior) with a `# CONCERNS.md` pointer. Reflect current state.

---

## Tech Debt

**Dead parameter — `detail(source=...)` is silently ignored:**
- Issue: `Report.detail(*columns, source=None)` accepts `source` but never stores or uses it — the body is only `self._detail = list(columns)` (`encino_rpt/report.py:282-293`). Detail rows always come from the primary dataset, unlike fields/groups/KPIs which honor `source` via `_enrich` (`encino_rpt/aggregation.py:130`) and `_build_group` (`encino_rpt/aggregation.py:193`).
- Files: `encino_rpt/report.py:282-293`, `encino_rpt/aggregation.py:123-152`
- Impact: A developer calling `detail(..., source="presupuesto")` silently gets primary-row data — a correctness trap with no error.
- Fix approach: Either drop the `source` kwarg from `detail()` (breaking the public signature) or plumb it through — introduce a per-detail source that `_build_instance`/`_build_path_group` consult when materializing `Detail` nodes, mirroring `_build_group`'s `sources.get(spec.source, sources[None])`.
- Regression: `tests/test_report.py:487-499` (`test_detail_source_ignored`, `xfail(strict=True)`).

**Dead parameter — `ExcelRenderer.styles` / `to_excel(styles=...)`:**
- Issue: `ExcelRenderer.__init__(styles=...)` stores `self.styles = styles or {}` (`encino_rpt/renderers/excel.py:23-26`) but `_walk`/`_chart`/`_pivot`/`_total_row` never read `self.styles`. `render(styles=...)` and `ReportResult.to_excel(styles=...)` (`encino_rpt/models.py:189-202`) thread the dict to a no-op.
- Files: `encino_rpt/renderers/excel.py:23-29,77-131`, `encino_rpt/models.py:189-202`
- Impact: `to_excel(styles={"bold": True})` silently does nothing — callers believe they're styling cells.
- Fix approach: Implement `styles` as a per-row-type style map (or remove it). If kept, apply it in `_total_row`/`_full_row`/`_write_value`.
- Regression: `tests/test_report_renderers.py:343-357` (`test_excel_styles_footer_dead_params` asserts the no-op doesn't crash).

**Dead parameter — `footer(column_position=...)`:**
- Issue: `Section.footer(column_position=...)` stores `GroupSpec.footer_column_position` (`encino_rpt/_specs.py:90`, set at `encino_rpt/section.py:37`) but no renderer reads it. Footers render as full-width rows: `_full_row` in `encino_rpt/renderers/excel.py:104-105`, HTML `encino_rpt/renderers/html.py:82-85`, text `encino_rpt/renderers/text.py:51-52`, CSV `encino_rpt/renderers/csv.py:62-63`, PDF `encino_rpt/renderers/pdf.py:103-104`.
- Files: `encino_rpt/_specs.py:90`, `encino_rpt/section.py:26-38`
- Impact: Footer alignment hint is discarded; output never honors it.
- Fix approach: Render footer aligned to the named column like `Total.column_position` is (`encino_rpt/renderers/excel.py:109-113`), or remove the param.

**Dead parameters — chart/pivot `source=`:**
- Issue: `ChartSpec.source` (`encino_rpt/_specs.py:50`) and `PivotSpec.source` (`encino_rpt/_specs.py:63`) are declared and set via `Section.chart/pivot(..., source=)` (`encino_rpt/section.py:84,120`), but `build_chart` (`encino_rpt/charts.py:8`) and `build_pivot` (`encino_rpt/pivot.py:10`) never receive or read them; `_build_instance` calls both with the already-selected `rows` (`encino_rpt/aggregation.py:354-367`). Contrast `KpiSpec.source`/`GroupSpec.source`, which are honored.
- Files: `encino_rpt/_specs.py:50,63`, `encino_rpt/aggregation.py:354-367`
- Impact: `chart(source=...)`/`pivot(source=...)` silently aggregate over the section's own rows regardless of `source`.
- Fix approach: Pass `spec.source` through to a `sources`-aware row selection, or drop the kwarg.

**`count` aggregate semantics are inconsistent:**
- Issue: `_value_for` (`encino_rpt/aggregation.py:71-88`) computes `count` three different ways: with an `expression` → `sum(1 for v in vals if v)` (truthy count, line 80-81); with `column` and no expression → `_aggregate("count", vals)` which filters `None` then `len(vals)` (non-None count, line 87-88); with neither → `len(rows)` (line 85-86). Same operator, three meanings.
- Files: `encino_rpt/aggregation.py:54-88`
- Impact: `count` over `[10, -5, 0]` yields `3` with `column=`, but `count(expression="monto > 0")` yields truthy-count semantics. Financial reports mixing both forms get surprising counts.
- Fix approach: Decide and document one contract (e.g., `count` = number of rows, `count(expression)` = number of truthy evaluations) and align `_value_for`.
- Regression: `tests/test_report.py:502-510` (`test_count_expression_semantics` asserts the current truthy behavior).

**Stale build artifacts:**
- Issue: `dist/` holds `encino_rpt-0.2.0-py3-none-any.whl` and `encino_rpt-0.2.0.tar.gz` while `pyproject.toml:10` declares `version = "0.2.1"`. `dist/` is gitignored and only rebuilt by CI (`uv build` in `.github/workflows/publish.yml:19`), so the local artifacts are one version behind.
- Files: `dist/encino_rpt-0.2.0-*`, `pyproject.toml:10`
- Impact: A developer installing from `dist/` locally gets 0.2.0, not 0.2.1.
- Fix approach: Rebuild `dist/` after a version bump, or delete it (gitignored; CI regenerates).

---

## Known Bugs

**`suppress_zero(column=...)` with a missing column suppresses every child:**
- Symptoms: `section("global").suppress_zero(column="columna_inexistente")` removes all children — `len(result.root.children) == 0`.
- Files: `encino_rpt/aggregation.py:428-444` (`_is_zero`), `encino_rpt/aggregation.py:373-385` (`_apply_order`)
- Trigger: `_is_zero` returns `v is None or v == 0`; for a `Group` child `child.key.get(column)` yields `None` when the column isn't in the key, so the child is treated as zero and filtered.
- Workaround: Use `suppress_zero(total=...)` with a named total instead, or ensure the column exists in the group key.
- Regression: `tests/test_report.py:471-484` (`test_suppress_zero_missing_column`, asserts the buggy 0-children behavior).

**`detail(source=...)` ignored — detail always uses primary rows:**
- Symptoms: `rep.detail("sku", "monto", source="presupuesto")` still renders primary-dataset rows.
- Files: `encino_rpt/report.py:282-293`
- Trigger: `source` kwarg is never consumed.
- Regression: `tests/test_report.py:487-499` (`test_detail_source_ignored`, `xfail(strict=True)`).

**Unhashable group column values crash with a raw `TypeError`:**
- Symptoms: Grouping by a column whose value is a `list`/`dict` raises `TypeError: unhashable type: 'list'`.
- Files: `encino_rpt/aggregation.py:178-189` (`_partition`, `key = tuple(r.get(c) for c in spec.columns)` at line 184); also `encino_rpt/pivot.py:16-19,49-56` (`_ordered_unique` `seen.add(v)` and `row_index`/`col_index` dicts keyed by raw values)
- Trigger: `tuple`/`dict` membership and dict-key lookups require hashable elements; the buggy path produces a tuple containing an unhashable element, then `key not in index` raises.
- Fix approach: Either validate group keys are hashable up-front with a clear `AggregationError`, or map unhashable keys to a stable string/normalized form.
- Regression: `tests/test_report.py:528-537` (`test_unhashable_group_value`, expects `TypeError`).

**Named totals with `None` value crash in the registry accumulator:**
- Symptoms: A named total whose value is `None` (e.g. `avg` over an all-`None` column) raises `TypeError` instead of recording `None`.
- Files: `encino_rpt/aggregation.py:214-236` (`_compute_totals_into`, `registry[key] = registry.get(key, 0) + val` at line 235)
- Trigger: `_aggregate("avg", ...)` returns `None` when the filtered value list is empty (`encino_rpt/aggregation.py:59`); then `0 + None` raises during registry registration. Same hazard for deferred `TOTAL()` references whose base total is `None`.
- Fix approach: Guard `val is None` when accumulating (`registry[key] = (registry.get(key, 0) or 0) + (val or 0)` or `0 if val is None`), or skip registration for `None` values.
- Regression: `tests/test_report.py:513-525` (`test_named_total_none_values`, `xfail(strict=True)`).

**chart/pivot expression errors are not wrapped with context:**
- Symptoms: A failing chart/pivot `expression` raises raw `ExpressionError` (or `ZeroDivisionError` re-wrapped by `evaluate`) with no group context, unlike totals/fields which go through `_wrap`.
- Files: `encino_rpt/aggregation.py:352-368` (`_build_instance` calls `build_chart`/`build_pivot` directly, no `_wrap`), `encino_rpt/aggregation.py:34-43` (`_wrap`), `encino_rpt/expressions.py:90-93`
- Trigger: `chart("bar", expression="1 / (monto - 1)")` on a row where `monto == 1` raises from inside `_value_for` (`encino_rpt/aggregation.py:79`) without the `{grupo}` prefix that totals get.
- Fix approach: Wrap the `fn(...)` calls at `encino_rpt/aggregation.py:358,367` with `_wrap(f"chart/pivot (grupo {spec.name!r})", fn, rows)`.
- Regression: `tests/test_report.py:540-555` (`test_chart_pivot_error_context`, `xfail(strict=True)`).

**Deep hierarchies crash `to_json()` / `model_dump()`:**
- Symptoms: A `path=` group tree of ~1100 levels renders fine in HTML/CSV/text/Excel, but `ReportResult.to_json()` raises `ValueError: Circular reference detected (depth exceeded)`.
- Files: `encino_rpt/renderers/json.py:25-27` (`to_dict` → `result.model_dump(mode="json")`), `encino_rpt/models.py:111-126` (recursive `Group.children`)
- Trigger: pydantic-core enforces a recursion depth limit (~1000) when serializing recursive models; the path-group builder can create arbitrarily deep trees (`encino_rpt/aggregation.py:238-307`).
- Fix approach: Serialize iteratively (e.g. explicit stack in `JsonRenderer.to_dict`) or document a depth ceiling for the JSON renderer.
- Regression: `tests/test_report_renderers.py:326-340` (`test_deep_tree_to_json`, expects the `ValueError`).

---

## Security Considerations

**Null-byte expression error is inconsistent across supported Python versions:**
- Risk: `evaluate("\x00", {})` produces different exception types per interpreter — raw `ValueError` on Python 3.10, `ExpressionError` (a `ValueError` subclass) on 3.11+.
- Files: `encino_rpt/expressions.py:55-64` (`except (RecursionError, MemoryError, SyntaxError)` does **not** catch `ValueError`)
- Current mitigation: None — the error still propagates, just with an inconsistent type. Not an injection vector (null bytes can't execute code), but it breaks the "one error contract" guarantee.
- Recommendations: Add `ValueError` to the `except` tuple at `encino_rpt/expressions.py:60`, normalizing null-byte input to `ExpressionError` on every supported version (CI matrix includes 3.10 — `.github/workflows/ci.yml:13`).
- Regression: `tests/test_security.py:155-159` (`test_expression_null_byte`).

**Formula-injection sanitization is otherwise solid:**
- The CSV/Excel formula sanitizer (`encino_rpt/renderers/_sanitize.py`) covers `= + - @ \t \r` prefixes and leading whitespace/BOM/`\x0c` via `_LEADING_TRIM` (`encino_rpt/renderers/_sanitize.py:7-16`). HTML CSS-injection is mitigated by `_SAFE_PROP`/`_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:21-22,164-182`). No outstanding injection vector detected.

---

## Performance Bottlenecks

**Deep-tree JSON serialization (see Known Bugs):**
- Problem: `model_dump()` hits pydantic-core's recursion limit (~1000) for deep path hierarchies, making JSON the only renderer that cannot emit deep trees.
- Files: `encino_rpt/renderers/json.py:27`, `encino_rpt/models.py:111-126`
- Cause: recursive pydantic model + depth-limited serializer.
- Improvement path: iterative serialization in `JsonRenderer.to_dict`, or an explicit documented depth cap.

**In-memory full-copy enrichment:**
- Problem: `build()` materializes an enriched copy of every dataset (`sources = {None: _enrich(...)}` plus one per `add_dataset`, `encino_rpt/aggregation.py:543-545`). `_enrich` copies each row (`dict(row)`) and appends computed fields (`encino_rpt/aggregation.py:123-152`). Memory is O(rows × (source columns + computed fields)).
- Cause: deliberate in-memory design; heavy aggregation is a documented non-goal (delegated to SQL `ROLLUP`/`CUBE`).
- Improvement path: None required for v1; consider streaming/lazy enrichment only if large-input support moves in-scope.

---

## Fragile Areas

**Grouping and pivoting assume hashable keys:**
- Files: `encino_rpt/aggregation.py:178-189`, `encino_rpt/pivot.py:16-34,49-56`
- Why fragile: dict/set keying breaks on `list`/`dict` cell values with a bare `TypeError`; no validation, no context, no clear message. `count_distinct` (`encino_rpt/aggregation.py:63,82-83`) also builds a `set`, so unhashable values crash there too.
- Safe modification: add up-front key-hashability validation (or normalization) before `_partition`/`build_pivot`/`count_distinct`.
- Test coverage: `test_unhashable_group_value` asserts the `TypeError`; no test covers unhashable pivot/count_distinct paths.

**Registry accumulation assumes numeric/None-safe addition:**
- Files: `encino_rpt/aggregation.py:235`
- Why fragile: `registry.get(key, 0) + val` crashes when a named total resolves to `None`; any new operator that can return `None` re-triggers this.
- Safe modification: centralize registry accumulation behind a helper that treats `None` as `0` (or skips registration), then reuse in both base-total and deferred paths.

**chart/pivot construction outside the `_wrap` context path:**
- Files: `encino_rpt/aggregation.py:352-368`
- Why fragile: unlike totals (`_compute_totals_into` wraps every `_value_for`, `encino_rpt/aggregation.py:221-230`), chart/pivot value functions are invoked raw, so failures lose group/field context. Adding new chart/pivot operators inherits the same gap.
- Safe modification: route chart/pivot `fn(...)` through `_wrap` with an explicit context string.
- Test coverage: `test_chart_pivot_error_context` is `xfail` (documents the gap).

---

## Scaling Limits

**JSON depth ceiling:**
- Current capacity: path hierarchies up to ~1000 levels serialize to JSON; beyond that `to_json()` raises `ValueError` (see Known Bugs). HTML/CSV/text/Excel have no such limit (iterative `walk`/path builder).
- Limit: pydantic-core recursion depth for recursive models.
- Scaling path: iterative JSON serialization or a documented depth cap.

**In-memory footprint:**
- Current capacity: all datasets + enriched copies held in memory simultaneously (`encino_rpt/aggregation.py:543-545`). Smoke test at 50k rows passes (<10s, `tests/test_perf_smoke.py:11-31`).
- Limit: linear in rows × columns; large financial extracts exhaust RAM rather than degrade gracefully.
- Scaling path: documented non-goal — aggregate server-side (SQL), feed `Report` already-materialized slices.

---

## Dependencies at Risk

**pydantic (runtime-only dependency, unpinned upper bound):**
- Risk: `pyproject.toml:33` declares `pydantic>=2` with no upper bound. The model layer relies on pydantic-v2-specific behavior — `Group.model_rebuild()` for the recursive union (`encino_rpt/models.py:232`), `PrivateAttr` for non-serialized context (`encino_rpt/models.py:124-126`), and `model_dump(mode="json")`.
- Impact: A future pydantic 3.x could change recursive-model serialization or `PrivateAttr`, silently breaking `to_json()`/`run()`.
- Migration plan: pin a `<3` (or otherwise tested) upper bound in `pyproject.toml`, and add a CI job against the latest allowed pydantic.

**Dev-tooling lower bounds only:**
- Risk: `pyproject.toml:49-56` declares `pytest>=9.1.1`, `ruff>=0.16.7`, `mypy>=2.3.1`, `pytest-cov>=7.1.0` with no upper bounds. Exact versions are pinned only in `uv.lock`.
- Impact: If `uv.lock` is regenerated, a newer mypy/ruff could emit new errors and break the `quality` gate (`ci.yml:46-53`).
- Migration plan: keep `uv.lock` committed and regenerated deliberately; consider upper bounds or a scheduled dependency refresh.

**Optional extras unpinned:**
- Risk: `pyproject.toml:37-38` declares `excel = ["openpyxl"]` and `pdf = ["reportlab"]` with no version constraints.
- Impact: `openpyxl`/`reportlab` APIs used by `encino_rpt/renderers/excel.py` and `encino_rpt/renderers/pdf.py` could change on a minor bump.
- Migration plan: pin tested minimums in the extras (or rely on `uv.lock` + periodic smoke tests).

---

## Missing Critical Features

**No server-side chart image rendering:**
- Problem: `chart` degrades to a summary table/string in every renderer except Excel (native charts in `encino_rpt/renderers/excel.py:215-249`). HTML/CSV/text/PDF emit a text summary only.
- Blocks: true graphical charts in HTML/PDF outputs. Explicitly deferred (v2 / `CHART-01`, matplotlib) in `.planning/REQUIREMENTS.md:61`.

**`column_position` is honored only in Excel totals:**
- Problem: `Total.column_position` is applied in Excel (`encino_rpt/renderers/excel.py:109-113`) but ignored by HTML/CSV/text/PDF; footer `column_position` is ignored everywhere (see Tech Debt).
- Blocks: aligned totals/footers in non-Excel outputs.

---

## Test Coverage Gaps

Coverage gate is `fail_under=80` with `branch = false` (`pyproject.toml:81-88`); branch coverage is off, so conditional paths in `_apply_order`/`_is_zero`/`_sort_key` are not measured. Specific untested paths:

**Excel native chart/pivot rendering:**
- What's not tested: `ExcelRenderer._chart` (`encino_rpt/renderers/excel.py:215-249`) and `ExcelRenderer._pivot` (`excel.py:251-265`) have no test asserting a native chart/pivot was actually added.
- Files: `encino_rpt/renderers/excel.py:215-265`
- Risk: chart/pivot output silently breaking.
- Priority: Medium.

**`_format` edge cases:**
- What's not tested: `format_value` for `kind="date"`, boolean values, and `excel_number_format` for `date`, non-scaled `percent`, and `symbol_position="suffix"`.
- Files: `encino_rpt/renderers/_format.py:9-76`
- Risk: date/suffix formatting regressions.
- Priority: Low.

**Multi-dataset KPI / field / chart / pivot sources:**
- What's not tested: `kpi(source=...)` (`encino_rpt/aggregation.py:486-504`), `add_field(source=...)` (`aggregation.py:130`), and the (dead) `chart(source=...)`/`pivot(source=...)` paths.
- Files: `encino_rpt/aggregation.py:486-504,123-152`
- Risk: the `source` plumbing for KPIs/fields is untested; dead chart/pivot source paths are unexercised.
- Priority: Medium.

**`order_by(column=...)` on `Detail` and `_sort_key` fallthrough:**
- What's not tested: ordering detail children by column (`encino_rpt/aggregation.py:416-421`) and the `return 0` fallback (`aggregation.py:425`).
- Files: `encino_rpt/aggregation.py:396-425`
- Risk: detail ordering regressions.
- Priority: Low.

**PDF chart/pivot and repeat-header paths:**
- What's not tested: `PdfRenderer` chart/pivot rendering and `repeat_header=False` (`encino_rpt/renderers/pdf.py:88-122,75`).
- Files: `encino_rpt/renderers/pdf.py`
- Risk: PDF layout regressions.
- Priority: Low.

---

## CI / Infrastructure

**Pre-existing GitHub Pages `configure-pages` failure (docs.yml):**
- Issue: The `Docs` workflow's `actions/configure-pages@v5` step fails (runs 3–7 in `failure`) while the `Build docs` (`uv run mkdocs build`) step passes. Registered in git history (commit `305a03d`). Not caused by, and does not block, the `test`+`quality` CI (which is green).
- Files: `.github/workflows/docs.yml:34` (`configure-pages@v5`), `.github/workflows/docs.yml:7-10` (permissions `pages: write`, `id-token: write`)
- Impact: Docs do not deploy to GitHub Pages (`https://hvalles.github.io/encino_rpt/`).
- Fix approach: Review GitHub Pages source/permissions in repo settings or adjust the workflow (e.g. `enablement`/`source` config for the Pages environment), then re-run.

---

*Concerns audit: 2026-09-17*
