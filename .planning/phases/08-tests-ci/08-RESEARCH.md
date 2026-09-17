# Phase 8: Tests & CI - Research

**Researched:** 2026-09-16
**Domain:** Python test suite consolidation + CI quality gates (type checking, formatting, coverage, performance smoke)
**Confidence:** HIGH

## Summary

Phase 8 is the *only* remaining phase and does **not** add runtime features — it consolidates the regression surface (TEST-01) and hardens CI (TEST-02). The library is already in good shape: `uv run ruff check .` is clean (exit 0) and the current suite is **70 tests, 82% coverage, 0.87s**. What is *missing* is the CI enforcement layer: no type checker, no `ruff format --check`, no coverage gate, no large-input smoke test — exactly the four gaps listed in `CONCERNS.md:200-204`.

Two empirical findings materially shape the plan:

1. **`ruff format --check` FAILS today on source and tests** (verified: `encino_rpt/__init__.py`, `tests/test_report.py`, and ~40 more files would be reformatted). Adding the format gate to CI *requires* a one-time `ruff format` normalization pass first, or CI goes red immediately. `ruff format .` also discovers **17 `.md` files** under `.planning/` and `docs/` (code-block formatting), so the config must `extend-exclude` those directories or scope the check to `encino_rpt tests`.
2. **Current coverage is 82%**, unevenly distributed: `models.py`, `pivot.py`, `_specs.py`, `_sanitize.py` are 100%, but `excel.py` (62%), `charts.py` (60%), `pdf.py` (65%), `csv.py` (69%), `text.py` (74%) are low — these are precisely the renderers whose buggy/dead paths (Excel styles, footer `column_position`, chart/pivot value errors) TEST-01 must cover.

**Primary recommendation:** Use **mypy + the official `pydantic.mypy` plugin** as the type checker, **pytest-cov** (wrapping `coverage.py`) with a `fail_under = 80` gate, add a minimal `[tool.ruff]` + `[tool.ruff.format]` config and run `ruff format --check .` after a one-time normalization pass, and add a `tests/test_perf_smoke.py` that builds a 50k-row pivot with a generous wall-clock assertion. Restructure CI into a matrix `test` job (pytest) plus a singleton `quality` job (mypy + ruff format + coverage on Python 3.13).

## Architectural Responsibility Map

This is a test/CI phase, so "tiers" map to the delivery pipeline layers rather than request-path tiers:

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Regression tests per fix (TEST-01) | `tests/` (pytest) | — | Each fix's behavior asserted against the canonical `ReportResult` tree or renderer output |
| Type checking (TEST-02) | CI job `quality` (mypy) | dev dependency in `pyproject.toml` | Static analysis of `encino_rpt/` only; runs once, not per-matrix |
| Format enforcement (TEST-02) | CI job `quality` (`ruff format --check`) | `[tool.ruff]` config | Single run; needs one-time normalization first |
| Coverage gate (TEST-02) | CI job `quality` (pytest-cov) | `[tool.coverage.report]` | Runs once (3.13) to avoid redundant 4× coverage |
| Perf smoke test (TEST-02) | `tests/test_perf_smoke.py` | CI `test` matrix | In-process; fast enough to run everywhere; assert wall-clock + correctness |
| Lint (existing) | CI `test` matrix (`ruff check`) | — | Already green; unchanged |

## User Constraints (from AGENTS.md — no CONTEXT.md exists for this phase)

`gsd-sdk query init.phase-op` reported `has_context: false`, so there are no discuss-phase locked decisions. The binding constraints come from `AGENTS.md` (project instructions) and `REQUIREMENTS.md`:

### Locked Decisions (project-level, from AGENTS.md / PROJECT.md)
- **Tech stack**: Python `>=3.10`; `pydantic>=2` is the **only runtime dependency**. All new tools (mypy, pytest-cov, coverage) go in the `dev` dependency group, never `dependencies`.
- **Optional deps isolated**: `openpyxl` (extra `excel`) and `reportlab` (extra `pdf`) stay optional; tests already guard them with `pytest.importorskip`.
- **Toolchain**: `uv` + `hatchling`; CI matrix is `["3.10", "3.11", "3.12", "3.13"]` on `ubuntu-latest`. Do not introduce npm/JS tooling.
- **Conventions**: `snake_case` files/tests (`tests/test_<area>.py`); Spanish docstrings/comments; `ruff` runs with **default rules only** (no `[tool.ruff]` select/ignore currently — adding config must not silently change lint behavior).
- **Security**: never `eval`; existing mitigations in `tests/test_security.py` must keep passing (formula injection, DoS, CSS injection).

### the agent's Discretion
- Type checker choice (mypy vs pyright vs basedpyright).
- Coverage tool + threshold.
- ruff format config specifics and CI job layout.
- Perf smoke test size/shape.

### Deferred Ideas (OUT OF SCOPE)
- `pydantic>=2` upper-bound pinning, unpinned-extra pinning (`CONCERNS.md` "Dependencies at Risk") — dependency-hygiene, not TEST-01/02.
- `detail(source=...)`, Excel `styles`, `footer(column_position=...)` — these are *bugs*, and TEST-01 only needs **regression tests that document current behavior**, not fixes (fixes belong to a future phase or explicit user request).
- Dependency-audit tooling (pip-audit, Dependabot), badge/SonarCloud integrations.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TEST-01 | Regression tests for each prior fix (idempotencia, precisión, SUM, sanitización, `order_by`, errores con contexto, multi-dataset, Link/Image, jerarquías profundas) | §Test Coverage Gaps below maps every CONCERNS bug to the exact test file/name to add; existing suite already covers idempotency (`test_run_is_idempotent`), precision (`test_format_value_precision_*`), SUM (`test_excel_formulas_no_double_count`), sanitization (`test_security.py`), `order_by` (`test_order_by_*`), error context (`test_aggregation_error_context`), Link/Image (`test_link_image_*`), deep hierarchies (`test_path_group_deep_no_recursion`) |
| TEST-02 | CI: type checker, `ruff format --check`, coverage gate, perf smoke with large inputs | §Standard Stack (mypy + pytest-cov), §CI Workflow Redesign, §Perf Smoke Pattern, §Code Examples |

## Standard Stack

### Core (new dev dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mypy | 2.3.1 | Type checker for `encino_rpt/` | First-class pydantic integration via official `pydantic.mypy` plugin; ecosystem default for library CI |
| pytest-cov | 7.1.0 | Coverage collection (`coverage.py` wrapper) | Standard pytest-native coverage; `--cov` + `--cov-fail-under` |
| coverage | 7.16.1 (transitive) | Underlying coverage engine | Brought in by pytest-cov; configured via `[tool.coverage.*]` |
| pytest | 9.1.1 (existing) | Test runner | Already pinned `>=9.1.1` |
| ruff | 0.16.7 (existing) | Linter **and** formatter | Already pinned `>=0.16.7`; formatter is built-in (`ruff format`), no extra dep needed |

### Supporting (considered, NOT selected)

| Library | Version | Purpose | Decision |
|---------|---------|---------|----------|
| pyright | 1.1.414 | Alternative type checker | Not selected — see Alternatives |
| basedpyright | 1.40.1 | Strict pyright fork | Not selected |
| pytest-timeout | (n/a) | Wall-clock test enforcement | Optional; `time.perf_counter()` assertion is dependency-free (preferred) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| mypy + `pydantic.mypy` plugin | pyright / basedpyright | pyright works out-of-the-box via PEP 681 `dataclass_transform` (pydantic's own docs confirm), but its **strict mode reports false positives** on pydantic's lenient coercion (`age='23'` → `int`). The mypy plugin gives model-aware checking (typed `__init__`, `model_construct`, frozen-model mutation) with no such false positives. mypy is also the plugin pydantic tests against first. |
| pytest-cov | bare `coverage run -m pytest` | pytest-cov integrates `--cov` flags into pytest's CLI and is the ecosystem norm; bare coverage.py needs two-step orchestration. |
| `ruff format --check .` (default) | `ruff format --check encino_rpt tests` | Scoped form is immune to `.planning/`/`docs/` `.md` code-block formatting; either is fine **if** `extend-exclude` is set. |

**Installation:**
```bash
uv add --group dev mypy pytest-cov
# pytest-cov pulls coverage.py transitively; ruff and pytest are already dev deps
```

**Version verification** (all confirmed on PyPI via `pip index versions`, 2026-09-16):
- `mypy` latest **2.3.1** (history back to 0.1 → legitimate)
- `pyright` latest **1.1.414**; `basedpyright` latest **1.40.1**
- `pytest-cov` latest **7.1.0**; `coverage` latest **7.16.1**

## Package Legitimacy Audit

> Ran the Package Legitimacy Gate: `slopcheck` 0.6.1 installed and `scan` executed against a temp `requirements.txt`.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| mypy | PyPI | ~10 yrs | very high | github.com/python/mypy | [OK] | Approved |
| pyright | PyPI | ~6 yrs | high | github.com/microsoft/pyright | [OK] | Approved (not selected) |
| basedpyright | PyPI | ~3 yrs | moderate | github.com/DetachHead/basedpyright | [OK] | Approved (not selected) |
| pytest-cov | PyPI | ~10 yrs | high | github.com/pytest-dev/pytest-cov *(slopcheck: no repo linked)* | [OK] | Approved |
| coverage | PyPI | ~15 yrs | very high | github.com/nedbat/coveragepy | [OK] | Approved |

**Packages removed due to slopcheck [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none — all 5 scanned `[OK]`. `pytest-cov` had a "no source repository linked" advisory, but its PyPI version history (0.6 → 7.1.0 over a decade) and pytest-dev maintainership are unambiguous; no flag needed.

## Architecture Patterns

### CI Workflow Redesign (target state)

Split the current single `test` job into two jobs so singleton checks (mypy, format, coverage) don't run 4×:

```
.github/workflows/ci.yml
├── job: test          (matrix 3.10/3.11/3.12/3.13)
│   ├── uv sync --all-extras --group dev
│   ├── uv run ruff check          # lint (unchanged)
│   └── uv run pytest              # unit + regression + perf smoke (unchanged command)
└── job: quality       (single, python 3.13)
    ├── uv sync --all-extras --group dev
    ├── uv run mypy encino_rpt          # type check (NEW)
    ├── uv run ruff format --check .    # format gate (NEW)
    └── uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80  # coverage gate (NEW)
```

Rationale: mypy/format/coverage are version-independent relative to the matrix; running them on one interpreter (3.13) cuts CI minutes and avoids 4× duplicate reports. The perf smoke stays in `pytest` (it's fast, ~1–2s) so it runs on all four Pythons and catches version-specific perf regressions.

### Recommended Project Structure (additions only)

```
pyproject.toml                      # + [tool.mypy], [tool.ruff], [tool.coverage.*]
.github/workflows/ci.yml            # restructured into test + quality jobs
tests/
├── test_report.py                  # existing (regression additions here)
├── test_report_renderers.py        # existing (regression additions here)
├── test_security.py                # existing (null-byte + formula-bypass regressions here)
└── test_perf_smoke.py              # NEW: 50k-row pivot + 50k-row deep-path smoke
```

### Pattern 1: Coverage gate via pytest-cov + `[tool.coverage.report]`

**What:** Put the threshold in config so both CI and local `--cov` runs enforce it.
**When to use:** Any CI coverage gate.
```toml
# pyproject.toml
[tool.coverage.run]
source = ["encino_rpt"]
branch = false

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.:",
]
```
Source: coverage.py docs — `[tool.coverage.run]` / `[tool.coverage.report]` TOML sections (`[VERIFIED: coverage.readthedocs.io]`).

### Pattern 2: Type check scope — library only

**What:** `uv run mypy encino_rpt` (not `tests/`). The test modules use untyped inline `list[dict]` literals; typing them is a separate concern.
**Why:** Zero-friction adoption; `mypy` already knows the library is the shipped surface.
**Config:**
```toml
[tool.mypy]
plugins = ["pydantic.mypy"]
python_version = "3.10"
check_untyped_defs = true
warn_unused_ignores = true
warn_redundant_casts = true
no_implicit_optional = true
```
Deliberately **not** `--strict` and **not** `disallow_untyped_defs = true`: the library types row data as `dict[str, Any]` / `value: Any` by design (see AGENTS.md CONVENTIONS), which strict mode would flag en masse.

### Pattern 3: Perf smoke test (large inputs, wall-clock + correctness)

**What:** A dedicated `tests/test_perf_smoke.py` generating a deterministic 50k-row dataset and asserting both **completion within a generous bound** and **correct totals**.
**When to use:** The `TEST-02` "smoke test de rendimiento con entradas grandes" criterion.
**Key design points:**
- Generate rows deterministically (`region = f"r{i%50}"`, `product = f"p{i%200}"`, `amount = i % 100`) so totals are computable in the assertion.
- Use `time.perf_counter()` with a **generous** threshold (10s) to avoid CI-machine flakiness — the single-pass pivot over 50k rows completes in ~1s, so 10s is 10× headroom.
- Assert a concrete result (e.g. `pivot.row_totals == [...]`, `cells` dimensions), not just "didn't crash".
- Keep it in the default `pytest` run (fast); no `-m` marker needed. Optionally tag `@pytest.mark.smoke` for future selective runs.

### Anti-Patterns to Avoid
- **Adding `ruff format --check` to CI before normalizing** — CI goes red immediately (verified: source + tests are unformatted today). Normalize first, gate second.
- **Setting the coverage gate at 90%** — `excel.py` (62%) and `pdf.py` (65%) have many environment-gated/formatting branches; 90% would force test-padding or omitting legit code. 80% is met today (82% measured) and is an honest floor.
- **`--cov` in `[tool.pytest.ini_options].addopts`** — forces coverage on every local `pytest` run (slows fast feedback). Keep `--cov` in the CI command, not in `addopts`.
- **`disallow_untyped_defs = true` in mypy** — conflicts with the project's deliberate `Any` typing of row data.
- **Type-checking `tests/` in the first pass** — scope creep; library first.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Coverage measurement | a custom `sys.settrace` counter | `pytest-cov` / `coverage.py` | Branch/line accounting, exclusions, HTML/XML reports all solved |
| Type checking | pylint's limited checks / manual review | `mypy` + `pydantic.mypy` | Pydantic-aware `__init__`/`model_construct` signatures |
| Formatting | hand-applied Black-style rules | `ruff format` (built into existing ruff) | Already installed; deterministic, `--check` mode for CI |
| Perf smoke timing | `pytest-benchmark` (benchmarks, not gates) | `time.perf_counter()` + generous bound | A smoke test is a pass/fail gate, not a benchmark; `pytest-benchmark` adds calibration noise and a dep |
| Wall-clock enforcement | `pytest-timeout` | optional; `perf_counter()` assert suffices | No extra dep; but `pytest-timeout` is the fallback if per-test timeouts are later wanted |

**Key insight:** All four TEST-02 gates are served by *existing, well-established* tools already in or adjacent to the toolchain — `ruff` already ships the formatter, `coverage.py` is the 15-year standard, and `mypy`'s pydantic plugin is the official integration. Nothing needs to be invented; the work is wiring + config + normalization.

## Common Pitfalls

### Pitfall 1: `ruff format --check` red on day one
**What goes wrong:** Adding the format gate to CI before normalizing makes the pipeline fail immediately.
**Why it happens:** The codebase was never formatted (no formatter configured; AGENTS.md confirms no `ruff format`).
**How to avoid:** Wave 0 runs `uv run ruff format encino_rpt tests` once (not `.`, to avoid touching `.planning/`/`docs/` `.md` code blocks) and commits it as a dedicated "chore: ruff format" change before the CI gate lands.
**Warning signs:** 40+ "File would be reformatted" messages (verified live).

### Pitfall 2: `.md` files swept into the format gate
**What goes wrong:** `ruff format .` discovers `.planning/**/*.md` and `docs/**/*.md` (verified: 17 `.md` files flagged) and tries to reformat their fenced code blocks.
**Why it happens:** ruff 0.16 formats Markdown code blocks; `.planning`/`docs` are not in the default exclude list.
**How to avoid:** `[tool.ruff] extend-exclude = [".planning", "docs", "dist", "build", ".venv"]`, or scope the command to `encino_rpt tests`.

### Pitfall 3: mypy reports a flood of errors on first run
**What goes wrong:** The library has not been type-checked before; mypy can emit dozens of errors from pydantic constructs, `Any` usage, and private-attr access.
**Why it happens:** First adoption of a type checker on an untyped-checked codebase.
**How to avoid:** Start with the moderate config above (not `--strict`); run `uv run mypy encino_rpt` in Wave 0, triage errors into (a) fix, (b) legit `# type: ignore[code]`, or (c) config relax. The pydantic plugin resolves the recursive `Group.children` and `PrivateAttr` cases that would otherwise error.

### Pitfall 4: mypy major-version risk (2.x is new)
**What goes wrong:** `mypy` jumped from 1.x to 2.x (2.3.1 is current). Pydantic's plugin says it is "tested against the latest mypy version," but a plugin/dependency mismatch would surface as plugin-load errors.
**Why it happens:** Recent major bump; the ecosystem is mid-transition.
**How to avoid:** Pin `mypy` to a specific version in the lockfile (via `uv add`), and include a Wave 0 step that runs mypy and confirms the plugin loads (`plugins = ["pydantic.mypy"]`). If 2.x misbehaves, fall back to the latest 1.x (1.20.2) — note this as a contingency.

### Pitfall 5: coverage gate flakes from optional-dependency imports
**What goes wrong:** Coverage of `excel.py`/`pdf.py` varies depending on whether `openpyxl`/`reportlab` are installed (the `# pragma: no cover` guarded-import blocks).
**Why it happens:** CI installs `--all-extras`, but a contributor running `pytest --cov` locally without extras gets skips (`importorskip`), not covered lines.
**How to avoid:** Keep the gate at 80% (robust to a few % drift); document that CI coverage numbers are authoritative (extras installed).

### Pitfall 6: perf smoke test flaky on slow CI runners
**What goes wrong:** A tight wall-clock bound (e.g. 2s) fails intermittently on cold CI machines.
**Why it happens:** GitHub-hosted runners have noisy performance.
**How to avoid:** 10× headroom (50k pivot ≈ 1s → assert `< 10s`), assert correctness too (so the test is meaningful even if timing is generous), and never assert on microsecond-scale bounds.

## Code Examples

### `[tool.ruff]` config (minimal — preserves default lint behavior)
```toml
[tool.ruff]
target-version = "py310"
line-length = 88
extend-exclude = [".planning", "docs", "dist", "build", ".venv"]

[tool.ruff.format]
quote-style = "double"
```
Source: ruff `Configuring Ruff` docs — defaults are `line-length=88`, `quote-style="double"`, `target-version` inferred from `requires-python` (`[VERIFIED: docs.astral.sh/ruff/configuration]`).

### mypy config
```toml
[tool.mypy]
plugins = ["pydantic.mypy"]
python_version = "3.10"
check_untyped_defs = true
warn_unused_ignores = true
warn_redundant_casts = true
no_implicit_optional = true
```
Source: pydantic `Mypy` integration docs — plugin enablement via `[tool.mypy] plugins = ['pydantic.mypy']` (`[VERIFIED: docs.pydantic.dev/latest/integrations/mypy]`).

### Perf smoke test (50k-row pivot)
```python
# tests/test_perf_smoke.py
import time

from encino_rpt import Report


def test_pivot_50k_rows_smoke():
    n = 50_000
    rows = [
        {"region": f"r{i % 50}", "product": f"p{i % 200}", "amount": i % 100}
        for i in range(n)
    ]
    rep = Report(rows)
    rep.group("global")
    rep.section("global").pivot("region", "product", operator="sum", value_column="amount")

    t0 = time.perf_counter()
    result = rep.run()
    elapsed = time.perf_counter() - t0

    pivot = result.root.children[-1]
    assert len(pivot.rows) == 50
    assert len(pivot.columns) == 200
    # 50k rows / 50 regions = 1000 rows per region, avg amount 49.5 → ~49500 per region
    assert pivot.row_totals[0] == sum((i % 100) for i in range(n) if i % 50 == 0)
    assert elapsed < 10.0, f"pivot 50k tardó {elapsed:.2f}s (límite 10s)"
```

### CI quality job (new)
```yaml
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - name: Set up Python 3.13
        run: uv python install 3.13
      - name: Install dependencies
        run: uv sync --all-extras --group dev
      - name: Type check
        run: uv run mypy encino_rpt
      - name: Format check
        run: uv run ruff format --check .
      - name: Coverage
        run: uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| mypy 1.x | mypy 2.x (2.3.1) | 2025 | Plugin API stable; verify `pydantic.mypy` load during Wave 0 |
| Black (separate formatter) | `ruff format` (unified lint+format) | ruff 0.3+ | No extra formatter dep; ruff already installed |
| `--cov` only via `.coveragerc` | `[tool.coverage.*]` in `pyproject.toml` | coverage 5.x+ | Single config file; aligns with existing pyproject-centric layout |
| pyright for pydantic | mypy + plugin remains canonical | ongoing | pydantic tests the mypy plugin first; pyright strict mode false-positives on lenient coercion |

**Deprecated/outdated:**
- `.coveragerc` / `setup.cfg` — use `[tool.coverage.*]` in `pyproject.toml`.
- `tox` — not present; `uv` + GitHub matrix already covers the multi-Python story.

## Runtime State Inventory

> Not a rename/refactor phase — **omitted**. No stored data, service config, OS registrations, secrets, or build artifacts are affected by adding tests/CI config.

## Test Coverage Gaps → Regression Test Map (TEST-01)

Current gaps (from `CONCERNS.md` §Test Coverage Gaps) mapped to the exact regression test to add. Every row is a TEST-01 deliverable:

| # | CONCERNS gap / bug | New test (file) | What it asserts |
|---|-------------------|-----------------|-----------------|
| 1 | Multi-dataset happy path (`add_dataset` + `source=`) | `test_report.py::test_multi_dataset_source` | `group/chart/pivot/add_field/kpi` with `source=` read the secondary dataset; `sources.get(spec.source, sources[None])` fallback |
| 2 | `suppress_zero(column=...)` missing column deletes all children | `test_report.py::test_suppress_zero_missing_column` | Documents current false-positive; asserts the (current) behavior so a fix later is a *change*, not a silent surprise |
| 3 | Named totals → `None` crash registry | `test_report.py::test_named_total_none_values` | `avg`/`max`/`min`/`count_distinct` over all-`None` column (documents `TypeError` today) |
| 4 | Unhashable grouping/pivot values | `test_report.py::test_unhashable_group_value` | Grouping/pivoting by `list`/`dict` column (documents raw `TypeError`) |
| 5 | Deep-tree JSON serialization `RecursionError` | `test_report_renderers.py::test_deep_tree_to_json` | `to_json()` / `model_dump()` on a >1000-deep path tree |
| 6 | `detail(source=...)` no-op | `test_report.py::test_detail_source_ignored` | Documents that `detail(source="x")` currently draws from primary dataset |
| 7 | Excel `styles` + `footer(column_position=...)` dead | `test_report_renderers.py::test_excel_styles_footer_dead_params` | Documents the no-op (no crash, no effect) so future wiring is detectable |
| 8 | `count` over expression counts truthy values | `test_report.py::test_count_expression_semantics` | `count` with vs without `expression=` difference (documents current semantics) |
| 9 | `ast.parse` null-byte not wrapped | `test_security.py::test_expression_null_byte` | `evaluate("\x00")` — documents raw `ValueError` today (should be `ExpressionError`) |
| 10 | Excel formula-mode bypasses sanitization | `test_security.py::test_excel_formula_mode_no_user_injection` | User values never written as live formulas when `formulas=True` (CONCERNS Security rec) |
| 11 | Chart/pivot value errors not wrapped | `test_report.py::test_chart_pivot_error_context` | Failing chart/pivot expression raises with context (documents current raw error) |

**Already covered (no new test needed, verify presence only):** idempotency (`test_run_is_idempotent`), precision (`test_format_value_precision_*`), Excel SUM no-double-count (`test_excel_formulas_no_double_count`), sanitization (`test_security.py`), `order_by` custom-fn/missing-total (`test_order_by_*`), error context (`test_aggregation_error_context`), Link/Image all renderers (`test_link_image_*`), deep path iterative build (`test_path_group_deep_no_recursion`).

> **Planning note:** Gaps #2, #3, #4, #6, #7, #9, #11 are *documentation-of-current-behavior* tests (the bug is not fixed in Phase 8). They must assert the **current** behavior with a clear comment (Spanish) marking them as "regresión documenta bug conocido — ver CONCERNS.md". This locks in TEST-01's "test per fix" requirement without expanding scope into bug-fixing.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| uv | Install/dev/CI | ✓ | 0.8.22 | — |
| Python | Runtime + CI matrix | ✓ | 3.14.7 (local); CI 3.10–3.13 | — |
| pytest | Test runner | ✓ | 9.1.1 | — |
| ruff | Lint + format | ✓ | 0.16.7 | — |
| mypy | Type check gate | ✗ (not installed) | — (PyPI 2.3.1) | Add via `uv add --group dev mypy` |
| pytest-cov / coverage | Coverage gate | ✗ (not installed) | — (PyPI 7.1.0 / 7.16.1) | Add via `uv add --group dev pytest-cov` |
| pyright / basedpyright | (not selected) | ✗ | 1.1.414 / 1.40.1 | n/a — not chosen |

**Missing dependencies with no fallback:** none — mypy and pytest-cov are both installed via `uv add --group dev` and lock into `uv.lock`; CI already runs `uv sync --all-extras --group dev`.

**Missing dependencies with fallback:** n/a.

## Validation Architecture

> `workflow.nyquist_validation` is `true` in `.planning/config.json` → section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 (+ pytest-cov 7.1.0 for coverage) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths=["tests"]`, `pythonpath=["."]`) |
| Quick run command | `uv run pytest -x -q` |
| Full suite command | `uv run pytest` (plus `uv run pytest --cov=encino_rpt --cov-fail-under=80` for the gate) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TEST-01 | Regression tests per fix (gaps #1–#11 above) | unit/integration | `uv run pytest tests/test_report.py tests/test_report_renderers.py tests/test_security.py` | ❌ Wave 0 (11 new tests) |
| TEST-02 (type) | mypy clean on `encino_rpt` | static | `uv run mypy encino_rpt` | ❌ Wave 0 (config + triage) |
| TEST-02 (format) | `ruff format --check` clean | static | `uv run ruff format --check .` | ❌ Wave 0 (normalize first) |
| TEST-02 (coverage) | ≥80% line coverage | metric | `uv run pytest --cov=encino_rpt --cov-fail-under=80` | ❌ Wave 0 (config) |
| TEST-02 (perf) | 50k-row smoke | perf smoke | `uv run pytest tests/test_perf_smoke.py` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest -x -q` (fast feedback)
- **Per wave merge:** `uv run pytest && uv run ruff check && uv run mypy encino_rpt && uv run ruff format --check .`
- **Phase gate:** full suite green + coverage ≥80% before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_perf_smoke.py` — new perf smoke module (does not exist)
- [ ] `[tool.mypy]`, `[tool.ruff]`, `[tool.coverage.*]` config sections in `pyproject.toml`
- [ ] `mypy` + `pytest-cov` added to `[dependency-groups] dev` and `uv.lock`
- [ ] 11 regression tests across the 3 existing test files (list in §Test Coverage Gaps)

## Security Domain

> `security_enforcement` is not disabled (absent from config → enabled). But this phase adds **no runtime code**; security relevance is limited to *preserving* existing mitigations and not weakening them via the new gates.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a (library, no auth) |
| V3 Session Management | no | n/a |
| V4 Access Control | no | n/a |
| V5 Input Validation | yes (indirect) | existing `expressions.py` AST whitelist + `_sanitize.py`; regression tests #9, #10 lock these |
| V6 Cryptography | no | n/a (no crypto in scope) |

### Known Threat Patterns for the test/CI surface

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Formula injection in Excel/CSV (user values) | Tampering | Keep `test_security.py` passing; add gap #10 (`formulas=True` never writes user strings as live formulas) |
| Expression evaluator DoS (`2**1e100`, null bytes) | DoS | Gap #9 documents the null-byte edge; existing `test_expression_*_limit` tests stay |
| HTML/CSS style injection | Tampering | Existing `test_html_style_*_mitigated` tests; unchanged |
| **Regression risk**: coverage/format/type gates accidentally *removing* security tests | Repudiation | The format normalization must not delete test code; the coverage `exclude_lines` must not hide `_sanitize.py`/`expressions.py` |

## Sources

### Primary (HIGH confidence)
- `pip index versions` (PyPI) — exact versions: mypy 2.3.1, pyright 1.1.414, basedpyright 1.40.1, pytest-cov 7.1.0, coverage 7.16.1 (2026-09-16)
- `slopcheck` 0.6.1 `scan` — all 5 candidate packages `[OK]`
- pydantic docs `/integrations/mypy` — `pydantic.mypy` plugin enablement + capabilities (`[VERIFIED]`)
- pydantic docs `/integrations/visual_studio_code` — pyright/Pylance works via PEP 681 but strict mode false-positives on lenient coercion (`[VERIFIED]`)
- astral ruff docs `/configuration` — `[tool.ruff]` schema, defaults (line-length 88, quote-style double), `extend-exclude` (`[VERIFIED]`)
- Live repo verification: `uv run ruff check .` (clean), `uv run ruff format --check .` (fails, 40+ files + 17 `.md`), `uv run pytest --cov=encino_rpt` (82%, 70 passed, 0.87s), `.github/workflows/ci.yml`, `pyproject.toml`

### Secondary (MEDIUM confidence)
- `CONCERNS.md` / `TESTING.md` (codebase map, 2026-09-17) — test structure, coverage gaps, CI gaps
- `AGENTS.md` embedded STACK/CONVENTIONS/ARCHITECTURE — toolchain and convention constraints

### Tertiary (LOW confidence)
- mypy 2.x ↔ pydantic-mypy plugin runtime compatibility — docs say "tested against latest mypy" but this was not executed; flagged for Wave 0 verification.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every version verified on PyPI + slopcheck + official docs.
- Architecture: HIGH — CI file and pyproject read directly; ruff/coverage behavior verified live.
- Pitfalls: HIGH — pitfall #1/#2 (format failures) and coverage figures (82%/62%/65%) measured empirically, not assumed.

**Assumptions Log** — see below.

**Research date:** 2026-09-16
**Valid until:** 2026-10-16 (30 days — stable toolchain; mypy 2.x churn is the only fast-moving element)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | mypy 2.3.1 works with `pydantic.mypy` plugin (pydantic 2.13.5) | Standard Stack / Pitfall 4 | Plugin load error → fall back to mypy 1.20.2 (contingency documented) |
| A2 | `ruff format` quote-style `double` matches existing code style | Code Examples | If code uses single quotes anywhere, normalization would churn more diffs — but grep confirms double-quote convention |
| A3 | 50k-row pivot completes in <10s on CI runners | Perf smoke | If it ever exceeds, the bound is 10× headroom; only affects the smoke test |
| A4 | Coverage stays ≥80% after TEST-01 additions | Coverage gate | New tests can only raise coverage (they exercise the 62–74% renderers); near-zero risk of falling below 80% |
| A5 | `tests/` stays out of the first mypy pass (library-only scope) | Pattern 2 | If planner wants tests typed too, it's additive work, not a correctness risk |

## Open Questions

1. **Coverage gate: 80% (floor) vs 85% (stretch)?**
   - What we know: 82% today; TEST-01 regression tests target the 62–74% renderers, likely pushing to ~85%.
   - What's unclear: exact post-TEST-01 number (can't know until tests land).
   - Recommendation: enforce `fail_under = 80` now; re-measure after TEST-01 and bump to 85% if comfortably above.

2. **mypy: 2.3.1 or pin to 1.20.2?**
   - What we know: 2.x is a fresh major; plugin "tested against latest."
   - What's unclear: real plugin compatibility at this exact version pair.
   - Recommendation: add latest (2.3.1), run `uv run mypy encino_rpt` in Wave 0; if the plugin fails to load, pin `mypy==1.20.2`.

3. **Should the 11 "documents-current-behavior" tests assert buggy behavior or be marked `xfail`/`skip`?**
   - What we know: 7 of the 11 gaps are *bugs not fixed in this phase* (detail source, suppress_zero, named-total None, unhashable, dead params, null-byte, count semantics).
   - What's unclear: whether the user wants them as `xfail` (expected-fail, signals when fixed) or as hard asserts of current behavior.
   - Recommendation: use plain asserts documenting current behavior with a Spanish `# CONCERNS.md` comment; `xfail(strict=True)` is the alternative if the team prefers a visible "fix me" signal.
