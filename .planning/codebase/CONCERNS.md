# Codebase Concerns

**Analysis Date:** 2026-09-17

> Scope: full repo. Reflects the post-pydantic state (commit `067bb21` migrated the 13 canonical models from pydantic to stdlib `@dataclass` + `encino_rpt/_serialize.py`, so the package now has **zero runtime dependencies**). The 7 Phase-11 engine bugs and the dead-param cleanup are **resolved** and listed only as "previously flagged — now fixed" at the bottom so the planner does not re-open them.

**Verification note:** coverage figures below were measured locally on CPython 3.11 (`uv run pytest --cov=encino_rpt --cov-report=term-missing`): 118 tests, 84.55% total (gate is 80%).

---

## Known Bugs

### Null byte in expressions: inconsistent error type across Python versions

- Symptoms: `evaluate("\x00", {})` raises a raw `ValueError` on Python 3.10, but an `ExpressionError` (subclass of `ValueError`) on Python 3.11+.
- Files: `encino_rpt/expressions.py:55-64` — `evaluate` wraps `ast.parse` with `except (RecursionError, MemoryError, SyntaxError)` (`expressions.py:60`) but does **not** catch `ValueError`. Regression pinned at `tests/test_security.py:166-170`.
- Trigger: A user-supplied expression containing a NUL byte. On 3.10 `ast.parse` raises `ValueError("source code string cannot contain null bytes")`, which escapes un-wrapped; on 3.11+ it raises `SyntaxError`, which is caught and wrapped as `ExpressionError`. (Confirmed locally on 3.14: `SyntaxError`.)
- Workaround: The test asserts only `pytest.raises(ValueError)`, which passes on every version because `ExpressionError` subclasses `ValueError` — so CI cannot detect the drift. Callers doing `except ExpressionError` silently miss the 3.10 raw `ValueError`.
- Fix approach: Add `ValueError` to the `except` tuple at `encino_rpt/expressions.py:60` and wrap it as `ExpressionError` for a uniform type across 3.10–3.13.

### `ReportResult.to_dict()` raises raw `RecursionError` on deep trees (guard only in JSON renderer)

- Symptoms: `result.to_json()` raises the controlled `ValueError("la jerarquía es demasiado profunda...")`, but `result.to_dict()` on the same deep tree raises a raw `RecursionError`.
- Files: `encino_rpt/models.py:165-174` (`ReportResult.to_dict` calls `to_jsonable(self)` directly, no guard); the `try/except RecursionError → ValueError` lives only in `encino_rpt/renderers/json.py:34-51` (`JsonRenderer.render`/`to_dict`). Regression only covers `to_json()` (`tests/test_report_renderers.py:467-479`).
- Trigger: A `path=` group with ~1100 levels. `to_json()` is safe; `to_dict()` and `from_dict()`/`from_json()` (`encino_rpt/models.py:176-202`) are not.
- Impact: The public `to_dict`/`from_dict`/`from_json` API (documented as the round-trip entry points after the pydantic removal) leaks `RecursionError` on adversarial or pathological inputs, while the JSON renderer contract promises a clear error. Inconsistent.
- Fix approach: Hoist the `RecursionError → ValueError` guard into `_serialize.to_jsonable` / `_serialize.from_dict`, or wrap `ReportResult.to_dict`/`from_dict`/`from_json` the same way `JsonRenderer` does.

---

## Tech Debt

### Loose reconstruction in `_serialize.from_dict` silently passes through malformed nodes

- Issue: `_coerce` (`encino_rpt/_serialize.py:65-93`) reconstructs the `Group.children` union (`Detail | Group | Chart | Pivot`) by the `type` discriminator via the hardcoded `_NODES` map (`_serialize.py:17-22`). When a child dict has no `type` key, an unknown `type`, or is a non-dict value, it falls through to `return value` at `_serialize.py:84` — i.e. the raw dict/scalar is left **in place** in `children` instead of being rejected.
- Impact: `ReportResult.from_dict({"root": {"type": "group", "children": [42, "foo"]}})` produces a `children` list containing `[42, "foo"]`. Downstream `walk()` (`encino_rpt/renderers/_walk.py`) only recognizes `Group`/`Detail`/`Chart`/`Pivot` and silently ignores unknown items, so this is silent data loss/corruption rather than a loud failure.
- Why it matters: pydantic previously validated every child against the union and raised `ValidationError` on unknown node types; the dataclass migration removed that safety net.
- Fix approach: In `_coerce`, when `origin` is a union of dataclass types and the value is a dict with no valid discriminator, raise `ValueError` naming the offending node; reject non-dict children of `Group.children`.

### `_serialize` also drops validation of model fields and ignores extra keys

- Issue: `_build` (`encino_rpt/_serialize.py:53-62`) skips absent keys (leaving `default_factory` defaults — intentional) but also **ignores** any unknown key, and performs no type/shape validation on the fields it does set. Direct construction of the exported models (`Format`, `Total`, `Group`, `Chart`, `Pivot`, `Kpi`, `ConditionalRule`, `Link`, `Image`, `Series`, `Detail`, `ReportMeta`, `ReportResult` — re-exported at `encino_rpt/__init__.py:21-36`) is likewise unvalidated: `Format(kind="bogus")` is silently accepted.
- Impact: `Report.set_format`/`add_style` re-validated their `Literal` enums manually in commit `b946ae2` (`encino_rpt/report.py:148-153,185-186`), but every other construction path (especially `from_dict`/`from_json` from untrusted JSON, and direct model instantiation) accepts invalid data.
- Fix approach: Add lightweight `__post_init__` validators to the dataclasses for the `Literal`-typed fields (mirroring what `set_format`/`add_style` do), or document that model validation is intentionally caller-responsibility post-migration.

### `_NODES` dispatch map must be maintained by hand

- Issue: The recursive `Group.children` union is no longer resolved by `Group.model_rebuild()`; instead `_serialize._NODES` (`encino_rpt/_serialize.py:17-22`) hardcodes the four node types. Adding a 5th node type to `children` requires editing both `models.py` and `_NODES`.
- Impact: Low today (node set is stable), but it is a silent extension point — a future node type forgotten in `_NODES` will be silently dropped on round-trip (see Loose reconstruction above).
- Fix approach: Derive `_NODES` from the actual type annotation of `Group.children` (via `get_type_hints`) instead of a literal dict.

### `column_position` honored only by the Excel renderer

- Issue: `Total.column_position` (`encino_rpt/models.py:56`) is threaded through `TotalSpec` (`encino_rpt/_specs.py:38`) and `Section.total()` (`encino_rpt/section.py:46`) and consumed only by `ExcelRenderer._walk` (`encino_rpt/renderers/excel.py:104-109`). HTML/CSV/Text/PDF/Markdown render totals as full-width rows or label/value pairs, ignoring it.
- Impact: `column_position="nota"` (`tests/test_report_renderers.py:349-360`) aligns only in Excel; every other format silently diverges. Not a correctness bug (value still emitted), but a documented-feature gap.
- Fix approach: Document `column_position` as Excel-only in `Section.total()`'s docstring, or implement alignment in the text-table renderers (larger effort).

### `ExcelRenderer` holds transient mutable state on `self`

- Issue: `ExcelRenderer.render()` assigns `self._ws`, `self._result`, `self._formulas`, `self._row` (`encino_rpt/renderers/excel.py:51-54`). `PdfRenderer` similarly sets `self._normal` during `render` (`encino_rpt/renderers/pdf.py:51`).
- Impact: Renderers are not re-entrant — concurrent/interleaved renders of the same instance corrupt each other. Low today (renderers are short-lived) but a latent footgun for async/threaded consumers.
- Fix approach: Move scratch state to locals or construct per-render state; drop instance-level scratch attributes.

### Perf smoke test relies on a wall-clock threshold

- Issue: `tests/test_perf_smoke.py:11-31` asserts a 50k-row pivot completes in `< 10.0s` via `time.perf_counter()`.
- Impact: Can flake on slow/oversubscribed CI runners despite correct behavior.
- Fix approach: Raise the ceiling, gate on a ratio (median of N runs), or move the timing gate to a non-blocking job.

---

## Security Considerations

The security posture is strong and was explicitly hardened (Phases 1/3/4). Verified current state:

- No `eval`/`exec`/`__import__`/`subprocess`/`pickle`/`os.` anywhere in `encino_rpt/`. Expressions go through the `ast` whitelist walker (`encino_rpt/expressions.py:55-123`) with `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`expressions.py:46-48`).
- OWASP formula-injection mitigation is centralized in `encino_rpt/renderers/_sanitize.py` (`is_dangerous`, `sanitize_csv`, `write_excel_cell`) and applied to CSV + Excel cells, headers, footers, totals, pivots, charts, and KPIs; leading whitespace/BOM is stripped before prefix detection (`_sanitize.py:9,14-16`).
- HTML conditional-style injection is mitigated via `_SAFE_PROP`/`_UNSAFE_VALUE` (`encino_rpt/renderers/html.py:22-23`) in both inline and `css=True` class modes.
- Template `{{param.N}}` is validated (numeric + in-range) and unresolved tokens raise `KeyError` (`encino_rpt/template.py:20-31`).

Remaining items:

### Null byte handling (see Known Bugs)

- Risk: A NUL byte in an expression yields inconsistent exception types across Python versions, which can bypass a caller's `except ExpressionError` on 3.10. It cannot execute code (still through the AST whitelist) — a robustness issue, not code-execution.
- Files: `encino_rpt/expressions.py:55-64`.
- Recommendation: Add `ValueError` to the caught set (see Known Bugs).

### `from_json`/`from_dict` accept untrusted JSON without validation

- Risk: With pydantic gone, `ReportResult.from_json(s)` (`encino_rpt/models.py:190-202`) parses arbitrary JSON and reconstructs nodes with no type/shape validation and no `RecursionError` guard (see Tech Debt). A malicious or malformed JSON document is silently accepted, and a deeply nested one raises a raw `RecursionError`.
- Files: `encino_rpt/_serialize.py`, `encino_rpt/models.py:176-202`.
- Recommendation: Validate node discriminators in `_coerce` and add the `RecursionError` guard in `from_dict`.

### No property-based/fuzz tests for the evaluator or sanitizers

- Risk: `expressions.py`, `_sanitize.py`, and `template.py` are covered only by hand-written cases (`tests/test_security.py`). A malformed-but-valid expression or unusual sanitizer input could regress silently.
- Recommendation: Add `hypothesis`-based tests asserting `evaluate` never raises anything other than `ExpressionError`/`ValueError` on arbitrary strings, and that `sanitize_csv`/`is_dangerous` never emit a live formula prefix.

---

## Performance Bottlenecks

### Deep-tree JSON serialization (recursion limit — now clearer, still a limit)

- Problem: `to_json()`/`JsonRenderer.render()` serialize via the recursive `to_jsonable` (`encino_rpt/_serialize.py:25-50`), which hits Python's recursion limit for deeply nested trees (a `path=` column with ~1100 levels). The engine builds the tree iteratively (`encino_rpt/aggregation.py:283-331`) and `walk()` (`encino_rpt/renderers/_walk.py`) is iterative, so HTML/CSV/Text/PDF/Markdown render fine — only JSON fails.
- Files: `encino_rpt/renderers/json.py:34-51` (catches `RecursionError` and raises a clear `ValueError`); regression at `tests/test_report_renderers.py:467-479`.
- Improvement path: The mitigation is a clear error, not a fix. A full fix requires an iterative JSON serializer or a pre-flight depth check. Note the residual gap: `ReportResult.to_dict()` (not `to_json()`) still leaks the raw `RecursionError` (see Known Bugs).

### In-memory aggregation (documented non-goal, but a real limit)

- Problem: The engine materializes every enriched row and group node in memory (`encino_rpt/aggregation.py:134-163` enrichment, `:189-234` partitioning). No spill-to-disk, no streaming input; readers also return full `list[dict]` (`encino_rpt/readers.py`).
- Impact: Memory grows linearly with row count × columns for very large inputs.
- Improvement path: Accepted as-is (heavy aggregates are delegated to SQL `ROLLUP`/`CUBE`). Only the smoke test (50k rows) bounds behavior.

---

## Fragile Areas

### `_serialize.py` (new, hand-rolled serialization)

- Files: `encino_rpt/_serialize.py`
- Why fragile: Replaces pydantic's `model_dump(mode="json")`/`model_validate` with ~105 lines of recursive custom logic. The `to_jsonable`/`_coerce` symmetry is subtle — a mismatch (e.g. `Decimal`/`datetime` handling, `_`-prefixed fields, `default_factory` defaults) would silently corrupt round-trips.
- Safe modification: Extend the round-trip test (`tests/test_report_renderers.py:419-447`) whenever touching it; keep `_NODES` in sync with `Group.children`.
- Test coverage: 92% — missing the `Decimal`/`datetime`/`Enum` branches (`_serialize.py:45-49`) and the single-dataclass-candidate branch (`:83`). **Decimal/datetime/Enum values are never serialized in any test.**

### Chart/pivot rendering across all renderers

- Files: `encino_rpt/renderers/html.py:137-162`, `csv.py:100-115`, `text.py:82-94`, `excel.py:211-261`, `pdf.py:118-162`, `markdown.py:102-148`; plus `encino_rpt/charts.py:35-46`.
- Why fragile: The only test that builds a `chart`/`pivot` is the serialization round-trip (`tests/test_report_renderers.py:435-439`, `tests/test_report.py:166,169`). **No renderer test exercises a chart or pivot**, so `walk()`'s `chart`/`pivot` events (`_walk.py:28-31`, 79% covered) are never driven through any renderer.
- Safe modification: Add at least one render test per format with a chart and a pivot before changing the event protocol.

---

## Scaling Limits

- **Recursion depth ~1000 for JSON round-trip** — `path=` trees beyond ~1000 levels cannot be serialized to JSON (clear `ValueError` now, but the limit stands). See Performance Bottlenecks.
- **Expression complexity caps** — `_MAX_NODES=1000`, `_MAX_DEPTH=100`, `_MAX_POW_EXP=10000` (`encino_rpt/expressions.py:46-48`) bound any single expression.
- **In-memory model** — no streaming input; whole `list[dict]` + enriched copies + group tree live in RAM. Fine for the documented use case; not for multi-million-row workloads.

---

## Dependencies at Risk

- **None at runtime.** `pyproject.toml` declares no `[project].dependencies` (pydantic fully removed in `067bb21`). Optional extras are lower-bound pinned: `openpyxl>=3.1.5`, `reportlab>=5.0.1` (`pyproject.toml:33-35`); dev/docs groups carry pytest/ruff/mypy/coverage/mkdocs (`pyproject.toml:45-58`).
- **Lower-bound pins are not exact pins** — `openpyxl`/`reportlab` may drift on minor releases; the `uv.lock` is the real pin and must be kept in sync on any bump. Consider documenting that reproducible installs rely on `uv.lock`, not the `>=` specifiers.
- **Stale build artifacts** — `dist/` still contains `encino_rpt-0.2.0-*` (version behind `0.2.2` in `pyproject.toml:10`). Harmless (gitignored, deploy rebuilds via `uv build` in `.github/workflows/publish.yml`), but a local `pip install dist/*.whl` can pick up the stale wheel.

---

## Missing Critical Features

None that block the current milestone. Deferred items are explicitly out of scope (`encino_rpt/REQUIREMENTS`-equivalent `.planning/REQUIREMENTS.md:108-115`): server-side aggregation/SQL generation, LaTeX renderer, `encinorm` integration, server-side chart images (matplotlib).

---

## Test Coverage Gaps

Measured `uv run pytest --cov=encino_rpt` (CPython 3.11, 118 tests, 84.55% total). Individual files well below the 80% gate:

| File | Coverage | Key untested paths |
|------|----------|--------------------|
| `encino_rpt/renderers/excel.py` | 66% | `_chart` (211-245), `_pivot` (247-261), `_apply_conditional` (192-209), KPI (57-63), Image (140-141) |
| `encino_rpt/renderers/markdown.py` | 68% | chart (135-145), pivot (102-110, 146-148), KPI (76-77), footer (132), `write` (87-90) |
| `encino_rpt/renderers/text.py` | 69% | chart (82-88), pivot (89-94) |
| `encino_rpt/renderers/pdf.py` | 75% | chart/pivot (118-128), Link/Image (133-139), `_pivot_table` (148-162), title/KPI (58-60) |
| `encino_rpt/charts.py` | 76% | `label_field` branches (39-41, 44-46) |
| `encino_rpt/renderers/_walk.py` | 79% | `chart`/`pivot` events (28-31) |
| `encino_rpt/renderers/csv.py` | 81% | chart (100-109), pivot (110-115) |
| `encino_rpt/aggregation.py` | 87% | `count`/`count_distinct`/`max`/`min` (61-69), `custom:` aggregate (84-88), `order_by` column/expression (448-458), `suppress_zero` (465-490) |
| `encino_rpt/_serialize.py` | 92% | `Decimal`/`datetime`/`Enum` (45-49), single-candidate (83) |

**Themes:**

1. **Chart/pivot rendering is untested in every format.** The only chart/pivot coverage is serialization round-trip (`tests/test_report_renderers.py:435-439`). `walk()`'s chart/pivot events and every renderer's chart/pivot branch are dead in the suite.
2. **Excel/Markdown/PDF optional-dependency renderers are thin.** These fall 5–18 points below the 80% gate individually; the aggregate is propped up by `models.py` (95%), `aggregation.py` (87%), `report.py` (93%). A regression in Excel conditional formatting, native charts, or PDF link/image rendering would pass CI.
3. **Aggregate operators beyond `sum`/`avg` are uncovered.** `count` (with a column), `count_distinct`, `max`, `min`, and `custom:` aggregates have no test (`encino_rpt/aggregation.py:61-69,84-88`). `order_by(column=...)`/`order_by(expression=...)` and `suppress_zero` error paths are likewise untested.
4. **New serialization edge cases uncovered.** `Decimal`, `datetime`/`date`/`time`, and `Enum` values are never serialized to JSON in any test (`encino_rpt/_serialize.py:45-49`), despite being a documented behavior (`Decimal`→`str`, `datetime`→isoformat).

**Priority:** Add render tests for chart/pivot across HTML/CSV/Text/Excel/PDF/Markdown (High), then aggregate-operator + `order_by`/`suppress_zero` correctness tests (Medium), then `Decimal`/`datetime` serialization round-trip (Medium).

---

## Still-Open: Infrastructure

### GitHub Pages is DISABLED on the repo (docs deploy fails)

- Issue: The `Docs` workflow `deploy` job fails at `actions/configure-pages@v5` because `GET /repos/hvalles/encino_rpt/pages` returns **404** — GitHub Pages is not enabled on the repository. The workflow itself is correct (permissions `pages: write`/`id-token: write` at `.github/workflows/docs.yml:7-10`, `configure-pages` + `upload-pages-artifact` + `deploy-pages`); `mkdocs build` passes.
- Files: `.github/workflows/docs.yml`
- Impact: Every push to `main` produces a red `Docs` check; published docs at `https://hvalles.github.io/encino_rpt/` are stale/absent.
- Fix approach: **Manual owner action, not a code fix** — Repo Settings → Pages → Source = "GitHub Actions" (enable Pages). No `docs.yml` change required.

---

## Previously Flagged — Now Fixed (do not re-open)

- **Phase 11 engine bugs (all resolved):** `detail(source=...)` at root / incompatible-with-groups (`encino_rpt/aggregation.py:596-602`); named total `None` no longer breaks the registry accumulator (`aggregation.py:256-259`); chart/pivot errors wrapped with group context (`aggregation.py:382-400`); `suppress_zero`/unhashable-grouping fail loudly with column names (`aggregation.py:196-207,461-490`, `encino_rpt/pivot.py:63-75`); `count` semantics documented/consistent (`aggregation.py:72-99`); deep-tree JSON now a clear `ValueError` (`encino_rpt/renderers/json.py:34-51`).
- **Dead params removed (commit `deae68b`):** footer `column_position`, chart/pivot `source`, `ExcelRenderer.styles` / `to_excel(styles=...)` no-ops.
- **pydantic removed (commit `067bb21`):** 13 models as stdlib `@dataclass`; `to_dict`/`from_dict`/`from_json` via `encino_rpt/_serialize.py`; zero runtime deps. (See Tech Debt / Known Bugs for the *new* concerns this introduced.)
- **`set_format`/`add_style` Literal validation restored** post-migration (`encino_rpt/report.py:148-153,185-186`, commit `b946ae2`).

---

*Concerns audit: 2026-09-17*
