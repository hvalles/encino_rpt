# Codebase Concerns

**Analysis Date:** 2026-09-17

> Scope: full repo. The 7 engine bugs from Phase 11 (`detail(source=)`, named-total `None`, chart/pivot context, `suppress_zero` missing column, unhashable grouping, `count` semantics, deep-tree JSON) are **RESOLVED** and are documented only as "previously flagged — now fixed" below. Dead params (`ExcelRenderer.styles`, footer `column_position`, chart/pivot `source`) were removed. `pydantic` is pinned `>=2,<3`, extras pinned with lower bounds, and streaming output (`iter_*` + `file=`) is implemented. Only the items below remain open.

---

## Still-Open: Infrastructure

### GitHub Pages is DISABLED on the repo (docs deploy fails)

- Issue: The `Docs` workflow (`deploy` job) fails at `actions/configure-pages@v5` because `GET /repos/hvalles/encino_rpt/pages` returns **404** — GitHub Pages is not enabled on the repository. The workflow itself is correct (permissions `pages: write` / `id-token: write` at `.github/workflows/docs.yml:7-10`, `configure-pages` + `upload-pages-artifact` + `deploy-pages`). The `mkdocs build` step passes.
- Files: `.github/workflows/docs.yml`
- Impact: Every push to `main` produces a red `Docs` check; published documentation at `https://hvalles.github.io/encino_rpt/` is stale or absent.
- Fix approach: **Manual owner action, not a code fix** — Repo Settings → Pages → Source = "GitHub Actions" (and enable Pages). No change to `docs.yml` required.

---

## Tech Debt

### `column_position` honored only by the Excel renderer

- Issue: `Total.column_position` is declared (`encino_rpt/models.py:53`), threaded through `TotalSpec` (`encino_rpt/_specs.py:38`) and `Section.total()` (`encino_rpt/section.py:46,59`), and used by `ExcelRenderer` to align a total under a specific column (`encino_rpt/renderers/excel.py:105-109`). The other five renderers (HTML, CSV, Text, PDF, Markdown) ignore it entirely — totals always render as a full-width row or a two-cell label/value pair.
- Impact: A user setting `column_position` sees the alignment only in Excel output; other formats silently diverge. Not a correctness bug (the value is still emitted), but a feature-completeness gap that can surprise.
- Fix approach: Either document `column_position` as Excel-only in `Section.total()`'s docstring, or implement alignment in the HTML/CSV/Text renderers (larger effort).

### `_partition` unhashable-detection does redundant work on the error path

- Issue: `_partition` builds the group key, calls `hash(key)`; on `TypeError` it re-iterates every column calling `hash(value)` to identify the offending column (`encino_rpt/aggregation.py:196-207`). This is a second full hash pass that only runs on the failure path, and the trailing `raise` (line 207) re-raises the raw `TypeError` for a case that cannot normally occur (tuple hash failure must come from an unhashable element).
- Impact: Negligible runtime cost (error path only); the trailing bare `raise` is a latent untyped error path.
- Fix approach: Identify the unhashable column in a single pass (e.g., by checking hashability while constructing the key), and drop the unreachable `raise`.

### `ExcelRenderer` holds transient mutable state on `self`

- Issue: `ExcelRenderer.render()` writes `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:51-54`). The renderer is not re-entrant — concurrent or interleaved renders of the same instance would corrupt each other.
- Impact: Low in practice (renderers are typically short-lived per render), but it is a latent footgun for any future async/threaded consumer.
- Fix approach: Pass state as locals/parameters or construct a fresh renderer per render; remove instance-level scratch attributes.

### Perf smoke test relies on a wall-clock threshold

- Issue: `tests/test_perf_smoke.py:11-31` asserts a 50k-row pivot completes in `< 10.0s` using `time.perf_counter()`. On slow/oversubscribed CI runners this can flake even though the algorithm is fine.
- Impact: Occasional false-red `test` job; not a product defect.
- Fix approach: Raise the ceiling, or gate on a ratio (e.g., "10x the median of 3 runs"), or move the timing gate to a separate non-blocking job.

---

## Known Bugs

### Null byte in expressions: inconsistent error type across Python versions

- Symptoms: `evaluate("\x00", {})` raises a raw `ValueError` on Python 3.10, but an `ExpressionError` (subclass of `ValueError`) on Python 3.11+.
- Files: `encino_rpt/expressions.py:55-64` (`evaluate` catches `RecursionError`, `MemoryError`, `SyntaxError` — but **not** `ValueError`); regression pinned at `tests/test_security.py:166-170`.
- Trigger: A user-supplied expression containing a NUL byte (`\x00`). On 3.10 `ast.parse` raises `ValueError("source code string cannot contain null bytes")`, which is not caught and propagates un-wrapped; on 3.11+ `ast.parse` raises `SyntaxError`, which is caught and wrapped as `ExpressionError`.
- Workaround: The test asserts only `pytest.raises(ValueError)`, so both paths pass. Consumers doing `except ExpressionError` would miss the 3.10 raw `ValueError`.
- Fix approach: Add `ValueError` to the `except` tuple in `evaluate` (line 60), wrapping it as `ExpressionError` for a uniform, documented error type across all supported Python versions (3.10–3.13).

---

## Security Considerations

The security posture is strong and was explicitly hardened (Phases 1, 3, 4). Verified current state:

- No `eval`/`exec` anywhere; expressions go through the `ast` whitelist walker (`encino_rpt/expressions.py:55-123`) with `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`encino_rpt/expressions.py:46-48`). No `__import__`, `subprocess`, `pickle`, or `os.` imports anywhere in `encino_rpt/`.
- OWASP formula-injection mitigation is centralized in `encino_rpt/renderers/_sanitize.py` (`is_dangerous`, `sanitize_csv`, `write_excel_cell`) and applied to CSV + Excel detail cells, headers, footers, totals, pivots, charts, and KPIs. Leading whitespace/BOM is stripped before prefix detection (`_sanitize.py:9,14-16`).
- HTML conditional-style injection is mitigated via `_SAFE_PROP` / `_UNSAFE_VALUE` regexes (`encino_rpt/renderers/html.py:22-23`) in both inline and `css=True` class modes; the `<style>` block reuses the same sanitizers (no new injection surface).
- Template `{{param.N}}` is validated (numeric + in-range) and unresolved tokens raise `KeyError` (`encino_rpt/template.py:20-31`).

Remaining items:

### Null byte handling (see Known Bugs)

- Risk: A NUL byte in an expression yields an inconsistent exception type across Python 3.10 vs 3.11+, which can bypass a caller's `except ExpressionError` handler on 3.10. It cannot execute code (still goes through the AST whitelist), so it is a robustness issue, not a code-execution risk.
- Files: `encino_rpt/expressions.py:55-64`.
- Recommendation: Normalize the exception type (add `ValueError` to the caught set), as above.

### No fuzzing / property-based tests for the expression evaluator or sanitizers

- Risk: The `ast` whitelist walker and the CSV/Excel sanitizers are only covered by hand-written cases (`tests/test_security.py`). A malformed-but-valid expression or an unusual sanitizer input could introduce a regression silently.
- Files: `encino_rpt/expressions.py`, `encino_rpt/renderers/_sanitize.py`, `encino_rpt/template.py`.
- Recommendation: Add property-based tests (e.g., `hypothesis`) asserting that arbitrary `str` inputs to `evaluate` never raise anything other than `ExpressionError`/`ValueError`, and that `is_dangerous`/`sanitize_csv` are idempotent and never emit a live formula prefix.

---

## Performance Bottlenecks

### Deep-tree JSON serialization (recursion limit)

- Problem: `to_json()`/`JsonRenderer.render()` serialize via pydantic's recursive `model_dump(mode="json")`, which hits Python's recursion limit / pydantic's depth limit for deeply nested trees (e.g., a `path=` column with ~1100 levels). The engine itself builds the tree iteratively (no recursion), and `walk()` (`encino_rpt/renderers/_walk.py`) is iterative, so HTML/CSV/Text/PDF/Markdown render fine — only JSON fails.
- Files: `encino_rpt/renderers/json.py:32-55` (catches `RecursionError`/depth `ValueError` and raises `ValueError("la jerarquía es demasiado profunda...")`); regression at `tests/test_report_renderers.py:436-448`.
- Cause: pydantic serialization is inherently recursive; no depth guard exists before serialization.
- Improvement path: Documented mitigation today (clear `ValueError`, no raw `RecursionError`). A full fix would require an iterative JSON serializer or a pre-flight depth check that rejects with a clearer bound earlier in the pipeline.

### In-memory aggregation (documented non-goal, but a real limit)

- Problem: The engine materializes every enriched row and every group node in memory (`encino_rpt/aggregation.py:134-163` enrichment, `:189-234` partitioning). No spill-to-disk, no streaming input. For very large inputs (> hundreds of thousands of rows) memory grows linearly with row count × columns.
- Files: `encino_rpt/aggregation.py`, `encino_rpt/readers.py` (readers also return full `list[dict]`).
- Cause: Documented design non-goal — heavy aggregates are delegated to SQL `ROLLUP`/`CUBE` (`AGENTS.md`).
- Improvement path: Accepted as-is. Only the smoke test (`tests/test_perf_smoke.py`, 50k rows) bounds behavior; larger inputs are the caller's responsibility.

---

## Fragile Areas

### `JsonRenderer.to_dict` depth-error detection is heuristic

- Files: `encino_rpt/renderers/json.py:58-60` (`_is_depth_error` matches on the substrings `"depth"`, `"circular"`, `"recursi"` in the exception message).
- Why fragile: Matching on error-message text is brittle across pydantic/Python versions — a wording change in pydantic could cause the `RecursionError`→`ValueError` mapping to miss, or (worse) misclassify an unrelated `ValueError` as a depth error.
- Safe modification: Prefer explicit `except RecursionError` (already the primary path at line 49) and treat the message-substring heuristic as a fallback; add a regression for a genuinely non-serializable value (already covered by `tests/test_report_renderers.py:451-460`, MA-01).

### `charts.py` `label_field` and no-children chart path

- Files: `encino_rpt/charts.py:22-23` (the `else` branch deriving labels from `own_totals`), `:39-46` (`_label` when `label_field` is set).
- Why fragile: These two branches have no test coverage (`charts.py` is at 68%; lines 22-23, 39-41, 44-46 are missed). A chart declared on a leaf group (no children) or using `label_field` could silently produce wrong labels.
- Safe modification: Add tests for (a) a chart on a group with no sub-groups (totals-derived labels) and (b) `label_field` pointing at a key vs. first row.

### Renderer event handlers for `chart`/`pivot` in CSV/Text/Markdown/PDF

- Files: `encino_rpt/renderers/csv.py:100-116`, `text.py:82-94`, `markdown.py:135-148`, `pdf.py:118-128`.
- Why fragile: These are the least-covered renderer paths (CSV 81%, Text 69%, Markdown 68%, PDF 75%). Chart/pivot rendering to non-HTML/Excel formats is thin and under-tested.
- Safe modification: Add cross-format golden tests asserting chart/pivot output shape in CSV, Text, Markdown, and PDF.

---

## Scaling Limits

### JSON serialization depth

- Current capacity: ~1000 levels of `path=` nesting serialize fine; beyond that `to_json()` raises `ValueError("la jerarquía es demasiado profunda...")` (`encino_rpt/renderers/json.py:9-12`). Regression pins 1100 levels → error (`tests/test_report_renderers.py:436-448`).
- Limit: pydantic recursion depth (no configurable bound exposed).
- Scaling path: Iterative JSON serializer, or a documented max-depth constant with an early, cheap pre-flight check in `ReportResult.to_json`.

### Pivot/group cardinality

- Current capacity: 50k rows × 50×200 pivot dimensions passes the smoke gate in <10s (`tests/test_perf_smoke.py`).
- Limit: `_partition` (`encino_rpt/aggregation.py:189-212`) and `build_pivot` (`encino_rpt/pivot.py`) are O(rows) single-pass; memory is the binding constraint for very high cardinality, not algorithmic cost.
- Scaling path: SQL-side pre-aggregation (documented non-goal).

---

## Dependencies at Risk

### `pydantic>=2,<3`

- Risk: Low. Upper bound is present (`pyproject.toml:33`), preventing a breaking v3 upgrade from silently entering. The `Group.model_rebuild()` forward-reference resolution (`encino_rpt/models.py:368`) and `PrivateAttr` usage are the two pydantic-v2 APIs the model layer depends on.
- Impact: A pydantic minor bump could change recursive-serialization depth behavior (see deep-tree concern).
- Migration plan: Periodically bump within `<3` and re-run the deep-tree + round-trip tests (`tests/test_report_renderers.py:436-460`, `tests/test_report.py`).

### `openpyxl>=3.1.5` and `reportlab>=5.0.1` (extras, lower-bound only)

- Risk: No upper pin on either optional dependency (`pyproject.toml:37-38`). A future major bump in `openpyxl`/`reportlab` could break the lazy-import renderers, but is outside the CI matrix until a consumer opts into the extra.
- Impact: Optional renderers (`ExcelRenderer`, `PdfRenderer`) are the first to break on a transitive major upgrade; they are also the lowest-coverage renderers (Excel 66%, PDF 75%).
- Migration plan: Pin upper bounds (e.g., `<4` for openpyxl, `<6` for reportlab) or add an extra CI job installing the extras to exercise `excel.py`/`pdf.py` against pinned versions.

---

## Missing Critical Features

### No depth bound is enforced at build time (only at JSON serialization)

- Problem: A `path=` group with an extreme depth builds a tree successfully and renders via all iterative renderers, but only fails when the user calls `to_json()`. The failure is discovered late, at a different layer than where the offending input was declared.
- Blocks: Predictable behavior for pathological `path` inputs; users cannot know in advance that JSON export will fail.
- Suggestion: Expose/document a max depth constant and validate (or warn) at `Report.run()` time.

### `column_position` only affects Excel (see Tech Debt)

- Problem: The alignment hint is silently ignored by five of six renderers.
- Blocks: Consistent presentation across output formats for reports that use column-positioned totals.

---

## Test Coverage Gaps

Overall coverage is 84% (above the 80% CI gate at `.github/workflows/ci.yml:53`), but several renderers are well below it and are not individually gated:

| Module | Coverage | Untested functionality |
|--------|----------|-------------------------|
| `encino_rpt/renderers/excel.py` | **66%** | KPIs (`:58-63`), chart (`:212-245`), pivot (`:248-261`), conditional formatting (`:200-209`), `_sum_formula` gaps (`:150`) |
| `encino_rpt/renderers/markdown.py` | **68%** | `write`/`iter` join logic (`:87-90`), pivot table (`:103-110`), chart/footer lines (`:132,135-148`) |
| `encino_rpt/renderers/text.py` | **69%** | `write`/`iter` (`:46-49`), chart/pivot lines (`:75,82-94`) |
| `encino_rpt/renderers/pdf.py` | **75%** | KPI/title (`:58,60`), chart/pivot/span logic (`:99,110,118-128`), `_pivot_table` (`:149-162`) |
| `encino_rpt/charts.py` | **68%** | no-children branch (`:22-23`), `label_field` (`:39-41,44-46`) |
| `encino_rpt/renderers/csv.py` | **81%** | chart/pivot serialization (`:100-113`) |
| `encino_rpt/renderers/_walk.py` | **79%** | Chart/Pivot event branches (`:28-31`) |
| `encino_rpt/readers.py` | **84%** | error paths: bad source type, raw `str`/`bytes` file-likes, `coerce` `float("nan")` guard, extension-less format |

Priority:

- **High:** `charts.py` `label_field` + no-children chart (silent wrong-label risk, `:22-23,39-46`).
- **High:** Excel chart/pivot + conditional formatting (`:200-261`) — the richest, least-tested renderer paths.
- **Medium:** `_walk.py` Chart/Pivot branches and CSV/Text/Markdown/PDF chart/pivot serialization (cross-format consistency).
- **Medium:** `readers.py` error paths (`:119-127,143-154,207-211,239-242,269,308,347`) — invalid source types and `coerce` edge cases.
- **Low:** `write`/`iter_*` streaming wrappers in text/markdown (already parity-checked by `test_iter_*_matches_render` in `tests/test_report_renderers.py:488-514`).

---

*Concerns audit: 2026-09-17*
