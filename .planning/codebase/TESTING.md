# Testing Patterns

**Analysis Date:** 2026-09-17

## Test Framework

**Runner:**
- `pytest` `9.1.1` (dev group, `pyproject.toml:50`)
- Config: `[tool.pytest.ini_options]` (`pyproject.toml:44-46`)
  - `testpaths = ["tests"]`
  - `pythonpath = ["."]`

**Coverage:**
- `pytest-cov` `7.1.0` (dev group, `pyproject.toml:55`), backed by `coverage` `7.16.1`
- Config: `[tool.coverage.run]` `source = ["encino_rpt"]`, `branch = false` (`pyproject.toml:81-83`); `[tool.coverage.report]` `fail_under = 80`, `show_missing = true`, `exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "if __name__ == .__main__.:"]` (`pyproject.toml:85-88`)

**Assertion Library:**
- Built-in `assert` statements only. No `pytest` assertion plugins, no `unittest.TestCase`, no `hamcrest`/`pytest-check`.

**Run Commands:**
```bash
uv run pytest                                     # Run all tests
uv run pytest tests/test_report.py                # Single file
uv run pytest -k "expression"                     # Filter by name
uv run pytest -x                                 # Stop at first failure
uv run pytest --cov=encino_rpt --cov-report=term-missing --cov-fail-under=80  # Coverage gate (CI)
```

## Test File Organization

**Location:**
- Separate top-level `tests/` directory (NOT co-located with source).

**Naming:**
- Files: `tests/test_<area>.py` — `test_report.py`, `test_report_renderers.py`, `test_security.py`, `test_readers.py`, `test_perf_smoke.py`
- Functions: `test_<behavior>` — `test_expression_arithmetic`, `test_csv_formula_injection`, `test_order_by_missing_total_raises`

**Structure:**
```
tests/
├── test_report.py             # expression evaluator + builder/aggregation + idempotency + regressions
├── test_report_renderers.py   # renderer output (html/csv/text/markdown/excel/pdf/json) + format_value
├── test_security.py           # formula injection, DoS limits, CSS injection, template validation
├── test_readers.py            # Report.read / encino_rpt.readers (CSV/TSV/JSON/JSONL/tuples/excel)
└── test_perf_smoke.py         # wall-clock perf smoke (50k rows, no benchmark framework)
```

## Test Structure

**Suite Organization:**
- Tests are grouped by section comment markers (`# --- <topic> ---`) rather than classes. Each test builds a `Report` fluently, runs it, then asserts on the canonical tree.

```python
# --- builder / agregación ---
def test_group_and_totals():
    rows = [
        {"agente": "Ana", "monto": 100},
        {"agente": "Ana", "monto": 50},
        {"agente": "Bob", "monto": 200},
    ]
    rep = Report(rows)
    rep.group("por_agente", columns="agente")
    rep.section("por_agente").header("Agente {{agente}}")
    rep.section("por_agente").total("sum", "monto")
    rep.group("global")
    rep.section("global").total("sum", "monto")
    result = rep.run()

    root = result.root
    assert root.name == "global"
    assert root.totals[0].value == 350
    assert len(root.children) == 2
```
(`tests/test_report.py:63-85`)

**Patterns:**
- Inline fixture data: each test builds its own `rows` list literal (no shared fixtures, no `conftest.py`).
- Assert on the pydantic tree directly: `result.root.children[0].row["total"] == 20.0`, `result.columns == [...]`, `result.kpis[0].value == 300`.
- Renderer tests assert on string output: `assert "<table>" in html_out`, `assert "A,2" in csv_out`, `assert pdf[:5] == b"%PDF-"`.
- Excel tests assert on `openpyxl` cell values: `ws["A1"].value == "sku"`, `cell.data_type == "s"`.
- Regression tests carry a tag in a comment referencing the ticket: `# CORR-11:`, `# CORR-08:`, `# TEST-01`, `# MA-01`, `# TMPL-01`, `# JSON-01`, `# P1`–`# P5`.

## Mocking

**Framework:** `pytest` built-ins only — `monkeypatch` fixture and `pytest.importorskip`. No `unittest.mock` in tests, no `pytest-mock` plugin.

**Patterns:**
```python
# Simulate a missing optional dependency (openpyxl) to exercise the ImportError branch
def test_excel_missing_extra(monkeypatch):
    monkeypatch.setitem(sys.modules, "openpyxl", None)
    with pytest.raises(ImportError):
        read_rows("datos.xlsx", format="excel")
```
(`tests/test_readers.py:160-163`)

**Skipping optional dependencies:**
```python
def test_excel_renderer():
    pytest.importorskip("openpyxl")
    ...
```
(`tests/test_report_renderers.py:208-209`, `tests/test_security.py:19-20`)

**What to Mock:**
- Optional dependency absence (`openpyxl`, `reportlab`) via `monkeypatch.setitem(sys.modules, ...)` and `pytest.importorskip` for skip-when-missing.

**What NOT to Mock:**
- The aggregation engine, renderers, and pydantic models are always exercised for real. No mocking of `Report`, `build()`, or `walk()` — tests run the full pipeline and assert on real output.

## Fixtures and Factories

**Test Data:**
- Inline `rows` list literals with small hand-picked data (2–3 rows typical), constructed at the top of each test.
- Large/synthetic data built with comprehensions in perf tests: `rows = [{"region": f"r{i % 50}", ...} for i in range(n)]` (`tests/test_perf_smoke.py:13-16`).

**Built-in fixtures used:**
- `tmp_path` — for writing real CSV/XLSX files: `path = tmp_path / "datos.csv"; path.write_text(...)` (`tests/test_readers.py:36-38`)
- `monkeypatch` — for dependency simulation (`tests/test_readers.py:160`)

**Local helper functions:**
- Module-level private helpers that build a reusable report: `_streaming_report()` (`tests/test_report_renderers.py:479-485`), consumed by multiple `iter_*`/`to_*_file` tests.

**Location:**
- No `conftest.py`, no `fixtures/` directory, no factory-boy. Fixtures are in-test or tiny local helpers.

## Coverage

**Requirements:**
- Enforced gate: `fail_under = 80` (`pyproject.toml:86`), enforced in CI via `--cov-fail-under=80` (`.github/workflows/ci.yml:53`).
- Current coverage ~84% (above the gate).
- `source = ["encino_rpt"]` scopes coverage to the package only (`pyproject.toml:82`).
- `show_missing = true` prints uncovered lines in `term-missing` output.
- `exclude_lines` (`pyproject.toml:88`) excludes `# pragma: no cover` (used for optional-dependency `ImportError` branches and environment-dependent code), `if TYPE_CHECKING:`, and `if __name__ == "__main__":`.

**View Coverage:**
```bash
uv run pytest --cov=encino_rpt --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Expression evaluator: `test_expression_arithmetic`, `test_expression_functions`, `test_expression_rejects_unsafe` (`tests/test_report.py:8-38`)
- Value formatting: `test_format_value_currency`, `test_format_value_percent`, `test_format_value_precision_*` (`tests/test_report_renderers.py:8-54`)
- Type coercion: `test_coerce_scalars`, `test_coerce_non_finite_kept_as_str` (`tests/test_readers.py:14-32`)
- Sanitization: `test_is_dangerous_leading_space_bom`, `test_sanitize_csv_leading_space_bom` (`tests/test_security.py:32-42`)

**Integration Tests:**
- Builder → aggregation → canonical tree: `test_basic_report_and_hidden_fields`, `test_group_and_totals`, `test_path_group` (`tests/test_report.py`)
- Builder → renderer output: `test_text_renderer`, `test_csv_renderer`, `test_html_renderer_and_styles`, `test_markdown_renderer`, `test_excel_renderer`, `test_pdf_renderer` (`tests/test_report_renderers.py`)
- Readers → builder: `test_read_csv_path`, `test_read_jsonl`, `test_excel_reader` (`tests/test_readers.py`)

**Security Tests (dedicated file `tests/test_security.py`):**
- Formula injection: CSV prefix (`test_csv_formula_injection`), Excel `data_type == "s"` (`test_excel_formula_injection`), leading space/BOM (`test_is_dangerous_leading_space_bom`)
- DoS limits: `test_expression_pow_limit`, `test_expression_complexity_limit`, `test_expression_float_exponent_limit`
- CSS/HTML injection: `test_html_style_injection_mitigated`, `test_html_style_value_injection_mitigated`, `test_html_css_mode_injection_mitigated`
- Template validation: `test_template_param_validation`, `test_unknown_template_token_raises`

**Perf Smoke Tests:**
- `tests/test_perf_smoke.py` — wall-clock bounded via `time.perf_counter()` (no `pytest-benchmark`, no markers). `test_pivot_50k_rows_smoke` asserts `elapsed < 10.0`. Structural complexity guards also live in `test_report.py` (`test_pivot_single_pass`, `test_path_group_deep_no_recursion`).

**E2E Tests:**
- Not used. No Selenium/Playwright; the library has no web UI. HTML output is asserted as string fragments.

## Common Patterns

**Error Testing (the dominant pattern):**
```python
with pytest.raises(ValueError, match="corte ya declarado"):
    rep.group("g", columns="a")
```
(`tests/test_report.py:357-358`)

```python
with pytest.raises(AggregationError, match="grupo 'global'"):
    rep.run()
```
(`tests/test_report.py:377-378`)

```python
with pytest.raises(ExpressionError):
    evaluate("__import__('os')", {})
```
(`tests/test_report.py:33-34`)

- Use `pytest.raises(ExceptionType, match="...")` with a Spanish substring to assert both type and message. Errors are raised at `run()` time, so the `rep.run()` call is inside the context manager.

**Idempotency Testing:**
```python
first = rep.run()
second = rep.run()
assert first.model_dump() == second.model_dump()
```
(`tests/test_report.py:347-349`)

**Round-trip Testing (pydantic serialization):**
```python
data = result.model_dump()
restored = ReportResult.model_validate(data)
assert restored.columns == ["sku", "cantidad"]
```
(`tests/test_report.py:303-311`)

**Streaming parity Testing:**
```python
result = _streaming_report()
assert list(result.iter_csv()) == result.to_csv().splitlines()
assert "".join(result.iter_html()) == result.render_html()
```
(`tests/test_report_renderers.py:488-514`)

**Async Testing:**
- Not applicable. The entire library is synchronous (no `async`/`await`, no event loop). No `pytest-asyncio`, no `asyncio` fixtures.

---

*Testing analysis: 2026-09-17*
