# Codebase Concerns

**Analysis Date:** 2026-09-17

> Scope: full repo (`encino_rpt/`, `tests/`, `.github/workflows/`, `pyproject.toml`).
> Verified against HEAD `0b14376` (v1.4 / `0.3.0`). 129 tests pass, coverage 91%.

## Resolved (do NOT re-flag)

The following were fixed in v1.4 — verified present, do not treat as open:

- **Null-byte / formula-injection bug** — FIXED. `_sanitize._LEADING_TRIM` strips `\s` and `\ufeff` BOM before checking `_DANGEROUS_PREFIXES` (`encino_rpt/renderers/_sanitize.py:7-9`), so a null byte no longer evades the `=`/`+`/`-`/`@`/`\t`/`\r` prefix check. Covered by `tests/test_security.py::test_expression_null_byte`, `test_is_dangerous_leading_space_bom`, `test_excel_leading_space_bom`.
- **`to_dict()` RecursionError** — FIXED. `to_jsonable`/`from_dict` catch `RecursionError` and re-raise `ValueError(DEPTH_ERROR)` (`encino_rpt/_serialize.py:30-46,113-129`). Covered by `tests/test_report_renderers.py:468-478,650-653`.
- **Coverage gaps: chart/pivot render, aggregate operators, Decimal/datetime** — FIXED. `test_chart_pivot_render_{html,csv,text,markdown,excel,pdf}` (`tests/test_report_renderers.py:602-635`), `test_aggregate_operators` (`tests/test_report.py:565-585`), `test_serialization_decimal_datetime` (`tests/test_report_renderers.py:689-706`).

## Tech Debt

**`column_position` is Excel-only (dead field in every other renderer):**
- Issue: `Total.column_position` is declared and threaded end-to-end (`encino_rpt/_specs.py:38`, `encino_rpt/section.py:46-67`, `encino_rpt/models.py:68`, `encino_rpt/aggregation.py:111`) but is only ever consumed by `ExcelRenderer` (`encino_rpt/renderers/excel.py:106-107`). CSV, HTML, PDF, Text, and Markdown renderers silently ignore the alignment hint.
- Impact: Users calling `section(...).total(..., column_position="x")` get no effect in 5 of 6 output formats; the parameter implies alignment that only Excel honors.
- Fix approach: either implement `column_position` in the other renderers (non-trivial for the flattened CSV/Text/Markdown layouts) or document it explicitly as an Excel-only presentation hint in `encino_rpt/section.py:59` and the README.

**Format/ConditionalRule `__post_init__` duplicates builder validation:**
- Issue: `Report.set_format` validates `kind`/`symbol_position`/`negative` (`encino_rpt/report.py:148-153`) and then `Format.__post_init__` re-validates the same three fields (`encino_rpt/models.py:48-54`). `Report.add_style` validates `when` (`report.py:185-186`) and `ConditionalRule.__post_init__` re-validates it (`models.py:124-126`).
- Impact: Redundant double validation on every `set_format`/`add_style` call. Harmless (and arguably defense-in-depth for direct `Format(...)`/`ConditionalRule(...)` construction), but the duplicated literal tuples can drift.
- Fix approach: keep the `__post_init__` guards as the single source of truth for direct construction and drop the pre-checks in the builder, OR centralize the allowed tuples in module-level constants shared by both.

## Known Bugs

None critical. Three minor informational items from the v1.4 review remain unpolished:

**`from_dict({"root": 42})` raises a raw `TypeError`:**
- Symptoms: `ReportResult.from_dict({"root": 42})` reaches `_build(Group, 42)` in `encino_rpt/_serialize.py:69-78`; the loop does `f.name not in data` against an `int`, raising `TypeError: argument of type 'int' is not iterable`.
- Trigger: A malformed payload where `root` (or any dataclass-valued field) is a scalar instead of a dict.
- Note: the *child*-node case IS handled cleanly — `from_dict({"root": {"type": "group", "children": [42]}})` raises a clear `ValueError` (`tests/test_report_renderers.py:663-671`). Only the top-level scalar is unpolished.
- Workaround: validate payload shape before `from_dict`; treat this as a cosmetic error-message gap rather than a data-loss bug.

**`link`/`chart` builders do not `Literal`-validate at the builder (late validation):**
- Symptoms: `Report.link(..., target="bogus")` (`encino_rpt/report.py:277`, `target: str`) and `Section.chart("bogus", ...)` (`encino_rpt/section.py:74`, `kind: str`) accept any string. The invalid value only surfaces later, when `Link.__post_init__` (`models.py:19-21`) or `Chart.__post_init__` (`models.py:96-98`) runs during aggregation.
- Impact: Violates the project's "validate early, return `self`" fluent-builder convention (`AGENTS.md` Conventions); the error is raised far from the offending builder call and wrapped as `AggregationError` with a context prefix rather than a direct `ValueError`.
- Fix approach: change `target`/`kind` to `Literal[...]` on the builder signatures and validate immediately (mirroring `set_format`/`add_style`).

## Security Considerations

**Expression evaluator DoS limits:**
- Risk: The AST whitelist evaluator is the security-critical surface (no `eval`, whitelist `ast` walk).
- Current mitigation: `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`encino_rpt/expressions.py:46-48`); covered by `tests/test_security.py` (`test_expression_pow_limit`, `test_expression_complexity_limit`, `test_expression_float_exponent_limit`).
- Status: Adequate. No action required; limits are generous enough for report expressions but bounded against hostile input.

**Formula injection (OWASP) — verified solid:**
- Risk: CSV/Excel cells beginning with `=`/`+`/`-`/`@`/`\t`/`\r` (after BOM/whitespace) being interpreted as formulas.
- Current mitigation: `is_dangerous`/`sanitize_csv`/`write_excel_cell` in `encino_rpt/renderers/_sanitize.py`, applied at every CSV cell write and every Excel cell write; `write_excel_cell` forces `cell.data_type = "s"` for dangerous values.
- Status: Solid, well-tested (`tests/test_security.py`). No action required.

## Performance Bottlenecks

**Perf smoke test uses a wall-clock threshold:**
- Problem: `tests/test_perf_smoke.py:31` asserts `elapsed < 10.0` seconds for a 50k-row pivot, measured with `time.perf_counter()`. Wall-clock time is non-deterministic on shared/loaded CI runners.
- Cause: A hard absolute wall-clock bound instead of a relative or statistical one.
- Improvement path: raise the ceiling (e.g. 30s) or make the assertion relative to a baseline (e.g. assert the pivot path is O(n) by comparing 10k vs 50k scaling), keeping a generous absolute ceiling only as a hard fail-safete. The current 10s for 50k rows is ~6x headroom on a healthy runner (test completes in ~1.6s locally), so it is mostly safe but not immune to cold CI.

## Fragile Areas

**Non-reentrant `ExcelRenderer` / `PdfRenderer`:**
- Files: `encino_rpt/renderers/excel.py:51-54` (`self._ws`, `self._result`, `self._formulas`, `self._row`), `encino_rpt/renderers/pdf.py:51` (`self._normal`).
- Why fragile: Both renderers stash transient render state on `self` during `render()`. Reusing a single renderer instance for concurrent or interleaved renders (threads, generators) corrupts output — the second render sees the first render's `_ws`/`_row`/`_normal`.
- Safe modification: pass render state as locals/parameters or create the state inside `render()`; never mutate `self` during a render.
- Practical severity: LOW — the public API always constructs a fresh renderer (`ReportResult.to_excel` → `ExcelRenderer(formulas=formulas)` at `models.py:403`; `to_pdf` → `PdfRenderer()` at `models.py:437`). Only direct `ExcelRenderer()`/`PdfRenderer()` reuse is affected.
- Test coverage: No test exercises instance reuse; the reentrancy hazard is untested.

## Scaling Limits

**Deep-tree JSON serialization depth (~1000 levels):**
- Current capacity: serialization/deserialization are recursive (`_to_jsonable` in `encino_rpt/_serialize.py:49-66`, `_coerce` at `:81-110`), so a `path`-grouped hierarchy deeper than Python's recursion limit (~1000) raises the controlled `ValueError(DEPTH_ERROR)`.
- Limit: ~1000 nesting levels for JSON round-trip. (Group *building* is immune — the path trie in `encino_rpt/aggregation.py:270-331` is iterative — but serialization is not.)
- Scaling path: rewrite `_to_jsonable`/`_coerce` with an explicit stack if arbitrarily deep reports must serialize. Currently a documented, clear error is raised (`DEPTH_ERROR`, `encino_rpt/_serialize.py:16-19`), which is acceptable for a financial reporter whose hierarchies are typically shallow.

**In-memory aggregation (documented non-goal):**
- Current capacity: entire input `list[dict]` and the canonical tree are held in memory; heavy aggregation is a documented non-goal delegated to SQL (`ROLLUP`/`CUBE`).
- Limit: unbounded memory for very large inputs; the 50k-row smoke test (`tests/test_perf_smoke.py`) is the only scale probe.
- Scaling path: out of scope by design — document, don't optimize.

## Dependencies at Risk

None critical. The library has **zero mandatory runtime dependencies** (`pyproject.toml:33-35` — only optional `excel`/`pdf` extras). Optional deps (`openpyxl>=3.1.5`, `reportlab>=5.0.1`) are lazily imported and raise `ImportError` with a Spanish install hint when absent (`encino_rpt/renderers/excel.py:40-46`, `pdf.py:35-48`). Dev/docs deps are pinned via `uv.lock`.

**GitHub Pages disabled on the repo (docs deploy fails until a manual Settings fix):**
- Risk: `pyproject.toml:39` advertises `Documentation = "https://hvalles.github.io/encino_rpt/"`, but the repository's GitHub Pages feature is disabled. `.github/workflows/docs.yml` builds and attempts to deploy, but `actions/deploy-pages` fails because Pages is not enabled on the repo.
- Impact: The published docs URL 404s until a maintainer enables Pages.
- Fix: manual, non-code — repo Settings → Pages → Source: "GitHub Actions". Not addressable from the codebase.

## Missing Critical Features

None blocking. Candidate gaps (low priority):

- **`column_position` unsupported in 5 of 6 renderers** (see Tech Debt) — a declared feature that silently no-ops outside Excel.
- **No `Literal` validation on `link`/`chart` builders** (see Known Bugs) — a consistency gap vs. the rest of the fluent API.

## Test Coverage Gaps

Overall 91% (`--cov-fail-under=80` enforced in `.github/workflows/ci.yml:53`). Remaining uncovered branches are mostly error paths and optional-dep code (openpyxl/reportlab chart/conditional generation). The previously-flagged gaps (chart/pivot render, aggregate ops, Decimal/datetime) are closed; the following remain:

**`encino_rpt/readers.py` (84%, 23 missed):**
- What's not tested: `TypeError` branches for non-list/non-dict JSON payloads (`readers.py:207,211,242`), `TypeError` for unsupported sources (`:119-127`), unregistered-reader `ValueError` (`:62-63`), format-resolution failure (`:347`), and the `ExcelReader` lazy-import path (`:308`).
- Risk: malformed-input error paths could regress unnoticed.
- Priority: Low–Medium (readers are the trust boundary for external input).

**`encino_rpt/aggregation.py` (90%, 36 missed):**
- What's not tested: error-wrapping branches in `_wrap` (`:40,43-44`), unknown-operator `ValueError` (`:69`), unregistered-custom-aggregate `AggregationError` (`:87,578-583`), and several deferred/edge paths (`:448-490,536,560`).
- Priority: Low (defensive error paths).

**`encino_rpt/renderers/excel.py` (87%, 24 missed):**
- What's not tested: KPI rendering (`:58-63`), `Link`/`Image` cell writing (`:131,141`), `_sum_formula` contiguous-range edge (`:150`), conditional style application (`:196-209`), and native chart writing (`:217-218`).
- Priority: Low — openpyxl chart/style output is environment-heavy and partially `pragma: no cover`.

**`encino_rpt/renderers/_format.py` (83%, 10 missed):**
- What's not tested: specific date/percent formatting branches (`:16-18,20,48,55-56,65,70,75`).
- Priority: Low.

**`encino_rpt/charts.py` (76%, 6 missed):**
- What's not tested: chart derivation fallback paths (`:39-41,44-46`).
- Priority: Low.

**Reentrancy (untested):**
- No test exercises reuse of a single `ExcelRenderer`/`PdfRenderer` instance (see Fragile Areas).

---

*Concerns audit: 2026-09-17*
