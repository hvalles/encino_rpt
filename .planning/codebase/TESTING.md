# Testing Patterns

**Analysis Date:** 2026-09-17

## Test Framework

**Runner:**
- **pytest** `9.1.1` (dev dependency, `pyproject.toml:50`)
- **pytest-cov** `7.1.0` (dev dependency, `pyproject.toml:55`)
- Config: `[tool.pytest.ini_options]` in `pyproject.toml:44-46`:
  - `testpaths = ["tests"]`
  - `pythonpath = ["."]` (allows `from encino_rpt import ...` without installation)

**Assertion Library:**
- Plain `assert` statements (no assertion helper library)

**Run Commands:**
```bash
uv run pytest                                                        # Run all tests
uv run pytest -v                                                     # Verbose
uv run pytest tests/test_report.py::test_group_and_totals           # Single test
uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80   # Coverage gate (as in CI)
uv run mypy encino_rpt                                               # Type check (CI quality job)
uv run ruff check                                                    # Lint (CI test job)
uv run ruff format --check encino_rpt tests                          # Format check (CI quality job)
```

## Test File Organization

**Location:**
- All tests live in a single top-level `tests/` directory (separate from source; no co-located `__init__.py`, no `conftest.py`)

**Naming:**
- `tests/test_<area>.py`:
  - `tests/test_report.py` — expression evaluator, builder, aggregation, totals, ordering, idempotency (555 lines)
  - `tests/test_report_renderers.py` — `format_value`, HTML/CSV/Excel/PDF/Text/JSON renderers, links/images (357 lines)
  - `tests/test_security.py` — formula injection, DoS limits, HTML/CSS injection, template param validation (178 lines)
  - `tests/test_perf_smoke.py` — wall-clock perf gate on a 50k-row pivot (31 lines)

**Structure:**
```
tests/
├── test_report.py            # engine + builder + regression/xfail
├── test_report_renderers.py  # renderers + format_value
├── test_security.py          # security mitigations
└── test_perf_smoke.py        # performance smoke gate
```

## Test Structure

**Suite Organization:**
- Flat top-level test functions (no classes, no fixtures, no `conftest.py`)
- Section banner comments group related tests: `# --- evaluador de expresiones ---`, `# --- builder / agregación ---`, `# --- idempotencia ---`, `# --- rendimiento ---` (`tests/test_report.py`); `# --- Link/Image ---`, `# --- layout (FEAT-02) ---` (`tests/test_report_renderers.py`); `# --- P1: inyección de fórmulas ---` (`tests/test_security.py`)
- Tests build a `Report(rows)` inline, configure it fluently, call `run()`, then assert on the returned `ReportResult`

**Patterns:**
- Setup: inline data + fluent builder, no setup/teardown hooks
- Assertion: direct `assert` on canonical model fields (`result.root.totals[0].value == 350`) or rendered output strings (`assert "<table>" in html_out`)
- Idempotency assertion: `assert first.model_dump() == second.model_dump()` (`tests/test_report.py:349`)
- No `pytest.raises(...)` without `match=`: every exception test pins the Spanish error message, e.g. `pytest.raises(ValueError, match="corte ya declarado")` (`tests/test_report.py:357`)

## Mocking

**Framework:** None. No `unittest.mock`, no `monkeypatch`, no `pytest-mock`.

**Patterns:** Tests exercise real objects end-to-end (integration-style). The only "fake" is a hand-rolled `value_fn` closure in `test_pivot_single_pass` (`tests/test_report.py:412-417`) used to count how many times groups are aggregated (single-pass assertion: `assert len(processed) == 3 + 2 + 2`).

**What to Mock:** Nothing — the library has no I/O or external services; heavy aggregates are delegated to SQL by design (non-goal).

**What NOT to Mock:** The expression evaluator, aggregation engine, and renderers are always tested against real implementations.

## Fixtures and Factories

**Test Data:** Inline `list[dict]` literals defined inside each test, e.g.:
```python
rows = [
    {"agente": "Ana", "monto": 100},
    {"agente": "Ana", "monto": 50},
    {"agente": "Bob", "monto": 200},
]
rep = Report(rows)
rep.group("por_agente", columns="agente")
rep.section("por_agente").total("sum", "monto")
```

**Location:** No shared fixtures/factories — data is local to each test function (a `conftest.py` is intentionally absent).

## Coverage

**Requirements:** `fail_under = 80` enforced via `[tool.coverage.report]` in `pyproject.toml:85-88`, run as `--cov-fail-under=80` in the CI `quality` job (`.github/workflows/ci.yml:53`).

**Coverage config** (`pyproject.toml:81-88`):
```toml
[tool.coverage.run]
source = ["encino_rpt"]
branch = false

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "if __name__ == .__main__.:"]
```
- `source = ["encino_rpt"]` — only library code is measured (tests excluded)
- `branch = false` — line coverage only
- `exclude_lines` matches the `# pragma: no cover - depende del entorno` markers on the optional-dep `ImportError` branches (`encino_rpt/renderers/excel.py:47`, `encino_rpt/renderers/pdf.py:41`)

**View Coverage:**
```bash
uv run pytest --cov=encino_rpt --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Expression evaluator (`tests/test_report.py:8-38`): arithmetic, functions, unsafe-node rejection
- `format_value` precision/formatting (`tests/test_report_renderers.py:8-55`): currency, percent, thousands, sci-notation extremes
- Sanitizers (`tests/test_security.py`): `is_dangerous`, `sanitize_csv` with space/BOM/`\x0c` prefixes

**Integration Tests:**
- Full report build → `run()` → `ReportResult` assertions (groups, totals, conditional totals, phase-B `TOTAL(...)`, cumulative, charts, pivots, order/top/suppress, KPIs)
- Renderers: each renderer tested by building a report and asserting on its output (`to_csv`, `to_text`, `render_html`, `to_excel`, `to_pdf`, `to_json`)
- JSON round-trip: `json.loads(result.to_json())` then `ReportResult.model_validate(data)` (`tests/test_report_renderers.py:289-306`)
- Model round-trip: `result.model_dump()` then `ReportResult.model_validate(data)` (`tests/test_report.py:303-311`)

**Performance Tests:**
- `tests/test_perf_smoke.py` — 50k-row pivot smoke gate using `time.perf_counter()` with a hard 10s wall-clock assertion: `assert elapsed < 10.0` (no `pytest-benchmark`, no markers)
- Deep-tree recursion guards: `test_path_group_deep_no_recursion` (1100-depth path, `tests/test_report.py:426-448`) and `test_deep_path_renders_iteratively` (`tests/test_report_renderers.py:309-322`)

**E2E Tests:** Not used (this is a library with no server/runtime).

## Common Patterns

**Error Testing:**
```python
with pytest.raises(ValueError, match="total de orden inexistente: 'total_inexistente'"):
    rep.run()
```
Multiple exception types are asserted separately (e.g. `test_template_param_validation` checks both `IndexError` and `ValueError`, `tests/test_security.py:88-93`).

**Optional dependency skipping:**
```python
def test_excel_renderer():
    pytest.importorskip("openpyxl")
    ...
```
`pytest.importorskip("openpyxl")` / `pytest.importorskip("reportlab")` guard every Excel/PDF test (`tests/test_report_renderers.py:99,116,135,165,177,201,240`, `tests/test_security.py:20,46,127,144,163`). Tests run against the `dev` dependency group which always installs `openpyxl` + `reportlab`, so these only skip on minimal environments.

**Known-bug regression tests (xfail):**
```python
@pytest.mark.xfail(
    strict=True,
    reason="bug conocido — ver CONCERNS.md §Known Bugs (detail(source=...) ignorado)",
)
def test_detail_source_ignored():
    ...
```
Three `strict=True` xfail tests document known bugs with a `CONCERNS.md` cross-reference:
- `test_detail_source_ignored` (`tests/test_report.py:487-499`)
- `test_named_total_none_values` (`tests/test_report.py:514-525`)
- `test_chart_pivot_error_context` (`tests/test_report.py:540-555`)

Other regression tests are *passing* but comment the bug they pin (e.g. `test_suppress_zero_missing_column`, `test_count_expression_semantics`, `test_unhashable_group_value`, `test_expression_null_byte`, `test_deep_tree_to_json`, `test_excel_styles_footer_dead_params`).

**Inline imports for internals under test:**
```python
from encino_rpt.aggregation import AggregationError   # inside the test function
from encino_rpt._specs import PivotSpec               # internal module accessed directly
from encino_rpt.pivot import build_pivot
```

**Test count:** ~82 tests total — 79 passed + 3 `xfail(strict=True)`.

**Async Testing:** Not applicable — the library is fully synchronous; no `async`/`await`, no `pytest-asyncio`.

---

*Testing analysis: 2026-09-17*
